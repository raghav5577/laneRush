import React from 'react'
import { Activity, Radio, ShieldAlert, Cpu, Sparkles, Play, MonitorPlay, Loader2 } from 'lucide-react'

export default function Navbar({ currentRun, mode, t, totalSteps, isLive, onOpenShowcase, onLaunchGui, isGuiRunning }) {
  return (
    <header className="bg-[#131A26] border-b border-[#1E293B] px-6 py-4 flex flex-wrap items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="bg-blue-600/20 border border-blue-500/30 p-2 rounded-xl text-blue-400">
          <Activity className="w-6 h-6 animate-pulse" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-white">LaneRush</h1>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
              v1.0
            </span>
          </div>
          <p className="text-xs text-slate-400">
            AI-Driven Adaptive Traffic Signal Control &amp; EV Green Corridor
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Launch SUMO-GUI Desktop Simulation Button */}
        <button
          onClick={onLaunchGui}
          disabled={isGuiRunning}
          className={`flex items-center gap-2 text-xs font-bold px-3.5 py-2 rounded-xl shadow-lg transition-all ${
            isGuiRunning
              ? 'bg-amber-500/20 border border-amber-500/50 text-amber-300 cursor-not-allowed'
              : 'bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-emerald-500/20 border border-emerald-400/30 hover:scale-105 active:scale-95'
          }`}
          title="Launch live microscopic SUMO-GUI simulation window on your desktop"
        >
          {isGuiRunning ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin text-amber-400" />
              <span>SUMO-GUI Running...</span>
            </>
          ) : (
            <>
              <MonitorPlay className="w-4 h-4 text-emerald-200" />
              <span>Launch SUMO-GUI</span>
            </>
          )}
        </button>

        {/* Evaluator Presentation Guide Button */}
        <button
          onClick={onOpenShowcase}
          className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold px-3.5 py-2 rounded-xl shadow-lg shadow-blue-500/20 border border-blue-400/30 transition-all hover:scale-105"
        >
          <Sparkles className="w-4 h-4 text-amber-300 animate-spin" />
          <span>Presentation Guide</span>
        </button>

        {/* Mode Badge */}
        <div className="flex items-center gap-2 bg-[#0B0F17] px-3 py-1.5 rounded-lg border border-[#1E293B]">
          <Cpu className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-medium text-slate-300">Mode:</span>
          <span className="text-xs font-bold text-emerald-400 uppercase tracking-wide">
            {mode || 'adaptive_corridor'}
          </span>
        </div>

        {/* Timestep Counter */}
        <div className="flex items-center gap-2 bg-[#0B0F17] px-3 py-1.5 rounded-lg border border-[#1E293B]">
          <Radio className={`w-4 h-4 ${isLive ? 'text-red-500 animate-pulse' : 'text-blue-400'}`} />
          <span className="text-xs font-medium text-slate-300">Sim Time:</span>
          <span className="text-xs font-mono font-bold text-blue-400">
            {t !== undefined ? `${t}s` : '0s'} {totalSteps ? `/ ${totalSteps}s` : ''}
          </span>
        </div>

        {/* Corridor Indicator */}
        <div className="flex items-center gap-2 bg-[#0B0F17] px-3 py-1.5 rounded-lg border border-red-500/30 text-red-400">
          <ShieldAlert className="w-4 h-4 text-red-400 animate-bounce" />
          <span className="text-xs font-bold">EV Pre-Clear Active</span>
        </div>
      </div>
    </header>
  )
}
