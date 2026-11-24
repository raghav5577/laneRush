import React, { useState, useEffect, useRef } from 'react'
import Navbar from './components/Navbar.jsx'
import KpiCards from './components/KpiCards.jsx'
import JunctionGrid from './components/JunctionGrid.jsx'
import CorridorTracker from './components/CorridorTracker.jsx'
import ControlPanel from './components/ControlPanel.jsx'
import ShowcaseModal from './components/ShowcaseModal.jsx'
import { Activity, Layers, Server } from 'lucide-react'

export default function App() {
  const [network, setNetwork] = useState(null)
  const [runsList, setRunsList] = useState([])
  const [selectedRunId, setSelectedRunId] = useState('')
  const [runData, setRunData] = useState(null)
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackSpeed, setPlaybackSpeed] = useState(1)
  const [selectedJunction, setSelectedJunction] = useState('A1')
  const [isLoading, setIsLoading] = useState(true)
  const [showcaseOpen, setShowcaseOpen] = useState(false)
  const [isGuiRunning, setIsGuiRunning] = useState(false)
  const [guiToast, setGuiToast] = useState('')

  const timerRef = useRef(null)

  // 1. Fetch initial network topology & runs list
  useEffect(() => {
    async function init() {
      try {
        const [netRes, runsRes] = await Promise.all([
          fetch('/api/network').then((r) => r.json()),
          fetch('/api/runs').then((r) => r.json()),
        ])
        setNetwork(netRes)
        setRunsList(runsRes)
        if (runsRes && runsRes.length > 0) {
          // Strongly prioritize adaptive_corridor runs with recorded decisions
          const corridorRun = runsRes.find(
            (r) => r.mode === 'adaptive_corridor' && r.has_decisions
          ) || runsRes.find((r) => r.mode === 'adaptive_corridor') || runsRes[0]
          setSelectedRunId(corridorRun.id)
        }
      } catch (err) {
        console.error('Failed to load initial data:', err)
      } finally {
        setIsLoading(false)
      }
    }
    init()
  }, [])

  // 2. Fetch run data when selectedRunId changes
  useEffect(() => {
    if (!selectedRunId) return
    async function loadRun() {
      setIsLoading(true)
      try {
        const res = await fetch(`/api/runs/${selectedRunId}/data`)
        const data = await res.json()
        setRunData(data)
        setCurrentStepIndex(0)
        setIsPlaying(false)
      } catch (err) {
        console.error('Failed to load run data:', err)
      } finally {
        setIsLoading(false)
      }
    }
    loadRun()
  }, [selectedRunId])

  // 3. Playback Loop
  useEffect(() => {
    if (isPlaying && runData && runData.timesteps && runData.timesteps.length > 0) {
      const intervalMs = Math.max(100, 1000 / playbackSpeed)
      timerRef.current = setInterval(() => {
        setCurrentStepIndex((prev) => {
          if (prev >= runData.timesteps.length - 1) {
            setIsPlaying(false)
            return prev
          }
          return prev + 1
        })
      }, intervalMs)
    } else {
      if (timerRef.current) clearInterval(timerRef.current)
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [isPlaying, playbackSpeed, runData])

  // Helper to jump directly to a simulation time t
  const handleJumpToTime = (targetT) => {
    if (!runData || !runData.timesteps || runData.timesteps.length === 0) return
    const index = runData.timesteps.findIndex((step) => step.t >= targetT)
    if (index !== -1) {
      setCurrentStepIndex(index)
      setIsPlaying(false)
    }
  }

  // Launch SUMO-GUI simulation on desktop
  const handleLaunchGui = async () => {
    try {
      setIsGuiRunning(true)
      const res = await fetch('/api/sim/launch-gui', { method: 'POST' })
      const data = await res.json()
      setGuiToast(data.message || 'SUMO-GUI launched! Check your desktop window.')
      setTimeout(() => setGuiToast(''), 6000)
    } catch (err) {
      console.error('Failed to launch SUMO-GUI:', err)
      setIsGuiRunning(false)
      setGuiToast('Failed to launch SUMO-GUI.')
      setTimeout(() => setGuiToast(''), 5000)
    }
  }

  // Poll GUI simulation status while running
  useEffect(() => {
    let pollInterval = null
    if (isGuiRunning) {
      pollInterval = setInterval(async () => {
        try {
          const res = await fetch('/api/sim/gui-status')
          const data = await res.json()
          if (!data.is_running) {
            setIsGuiRunning(false)
            setGuiToast('SUMO-GUI simulation completed! New run loaded.')
            setTimeout(() => setGuiToast(''), 5000)
            const newRuns = await fetch('/api/runs').then((r) => r.json())
            setRunsList(newRuns)
            if (data.last_run_id) {
              setSelectedRunId(data.last_run_id)
            }
          }
        } catch (e) {
          console.error('Status check error:', e)
        }
      }, 2000)
    }
    return () => {
      if (pollInterval) clearInterval(pollInterval)
    }
  }, [isGuiRunning])

  const currentStep = runData?.timesteps?.[currentStepIndex] || {}
  const totalSteps = runData?.timesteps?.length || 0
  const selectedDecision = currentStep?.junctions?.[selectedJunction] || {}

  return (
    <div className="min-h-screen bg-[#070B11] text-slate-100 flex flex-col font-sans relative">
      {/* Floating Status Toast */}
      {guiToast && (
        <div className="fixed bottom-6 right-6 z-50 bg-[#1E293B] border border-emerald-500/50 text-white px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 animate-slideUp">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
          <span className="text-xs font-semibold">{guiToast}</span>
        </div>
      )}

      {/* Evaluator Presentation Showcase Modal */}
      <ShowcaseModal
        isOpen={showcaseOpen}
        onClose={() => setShowcaseOpen(false)}
        onJumpToTime={handleJumpToTime}
        onLaunchGui={handleLaunchGui}
        isGuiRunning={isGuiRunning}
      />

      {/* Top Navigation */}
      <Navbar
        currentRun={selectedRunId}
        mode={runData?.meta?.mode || 'adaptive_corridor'}
        t={currentStep?.t || 0}
        totalSteps={runData?.timesteps?.[totalSteps - 1]?.t}
        isLive={false}
        onOpenShowcase={() => setShowcaseOpen(true)}
        onLaunchGui={handleLaunchGui}
        isGuiRunning={isGuiRunning}
      />

      {/* Main Dashboard Body */}
      <main className="flex-1 p-6 flex flex-col gap-5 max-w-[1600px] w-full mx-auto">
        {/* KPI Cards */}
        <KpiCards
          meanWait={runData?.mean_wait_s}
          maxWait={runData?.max_wait_s}
          evTransit={runData?.ev_trips?.[0]?.duration}
          completedCount={runData?.completed_count}
          corridorEvents={runData?.corridor_events_count}
        />

        {/* Central Map & Tracker Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 flex-1">
          {/* Left Column: 3x3 Junction Map (7 Cols) */}
          <div className="lg:col-span-7 flex flex-col">
            <JunctionGrid
              network={network}
              currentStep={currentStep}
              selectedJunction={selectedJunction}
              onSelectJunction={(id) => setSelectedJunction(id)}
            />
          </div>

          {/* Right Column: EV Corridor Tracker & Junction Inspector (5 Cols) */}
          <div className="lg:col-span-5 flex flex-col gap-5">
            <CorridorTracker currentStep={currentStep} />

            {/* Junction Inspector Card */}
            <div className="bg-[#131A26] border border-[#1E293B] rounded-2xl p-5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-blue-400" />
                  <h3 className="text-sm font-bold text-white">
                    Junction Inspector: <span className="text-blue-400">{selectedJunction}</span>
                  </h3>
                </div>
                <span className="text-xs font-mono text-slate-400">
                  Phase: {selectedDecision.target_phase !== undefined ? selectedDecision.target_phase : '0 (NS)'}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-[#0B0F17] p-3 rounded-xl border border-[#1E293B]">
                  <p className="text-[11px] text-slate-400 uppercase font-semibold">Active Decision</p>
                  <p className="text-xs font-mono font-bold text-emerald-400 mt-1">
                    {selectedDecision.action
                      ? `${selectedDecision.action.toUpperCase()} (${(selectedDecision.reason || 'stay').toUpperCase()})`
                      : 'HOLD (STAY)'}
                  </p>
                </div>

                <div className="bg-[#0B0F17] p-3 rounded-xl border border-[#1E293B]">
                  <p className="text-[11px] text-slate-400 uppercase font-semibold">Rush Scores</p>
                  <p className="text-xs font-mono text-slate-300 mt-1">
                    NS:{' '}
                    <span className="text-emerald-400 font-bold">
                      {(selectedDecision.scores?.phase_0 || 0).toFixed(0)}
                    </span>{' '}
                    | EW:{' '}
                    <span className="text-blue-400 font-bold">
                      {(selectedDecision.scores?.phase_2 || 0).toFixed(0)}
                    </span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Playback & Run Controls */}
        <ControlPanel
          isPlaying={isPlaying}
          onTogglePlay={() => setIsPlaying(!isPlaying)}
          onReset={() => setCurrentStepIndex(0)}
          currentStepIndex={currentStepIndex}
          totalSteps={totalSteps}
          onSeek={(idx) => setCurrentStepIndex(idx)}
          playbackSpeed={playbackSpeed}
          onChangeSpeed={(spd) => setPlaybackSpeed(spd)}
          runsList={runsList}
          selectedRunId={selectedRunId}
          onSelectRun={(id) => setSelectedRunId(id)}
        />
      </main>

      {/* Footer */}
      <footer className="border-t border-[#1E293B] py-3 px-6 text-center text-xs text-slate-500">
        LaneRush Simulation Platform — DeepMind Evaluation Grade Control Suite
      </footer>
    </div>
  )
}
