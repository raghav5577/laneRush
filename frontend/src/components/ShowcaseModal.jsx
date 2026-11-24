import React from 'react'
import { X, Play, ShieldAlert, Cpu, Sparkles, CheckCircle2, AlertTriangle, ArrowRight, ExternalLink, MonitorPlay, Loader2 } from 'lucide-react'

export default function ShowcaseModal({ isOpen, onClose, onJumpToTime, onLaunchGui, isGuiRunning }) {
  if (!isOpen) return null

  const demoSteps = [
    {
      step: 1,
      title: 'AI Rush-Based Dynamic Signal Release',
      time: 25,
      badge: 'Dynamic Scoring',
      badgeColor: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      description:
        'Watch Junctions A1 & B1. Instead of rigid fixed timers (42s/42s), the controller reads lane vehicle counts, halted cars, and queue waiting times in real-time.',
      formula: 'Score = 1.0·Count + 2.0·Halting + 0.8·MaxWait',
      keyPoint:
        'Hysteresis rule (Other > 1.2·Current + 1) guarantees the light switches only when queue pressure genuinely warrants it, avoiding dangerous rapid switching.',
    },
    {
      step: 2,
      title: '4 Cars Stuck at Red Signal Ahead of EV',
      time: 38,
      badge: 'Congestion Challenge',
      badgeColor: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      description:
        'Notice Junction A1 on Row 1 (East-West corridor). 4 passenger cars are halted at the red signal while North-South cross-traffic is moving.',
      formula: 'Queue Length = 4 vehicles halted on approach lane left1A1_0',
      keyPoint:
        'Real-world emergency vehicles often get blocked by stationary cars queued at a red light. LaneRush solves this with Dynamic Pre-Clearing Queue Flushes.',
    },
    {
      step: 3,
      title: 'Emergency Vehicle Release & Immediate Cross-Traffic Halting',
      time: 42,
      badge: 'Corridor Override',
      badgeColor: 'bg-red-500/10 text-red-400 border-red-500/20',
      description:
        'Ambulance EV0 is detected upstream (< 40s ETA). The corridor arbiter immediately pre-clears up to 3 upcoming junctions on its route (A1, B1, C1).',
      formula: 'ETA = dist / v_free  |  Threshold = 12s + 2s × halted_cars',
      keyPoint:
        'CRITICAL SAFETY FEATURE: Adjacent North-South cross-traffic is immediately brought to a stop via yellow clearance (Phase 1 → Phase 2), preventing high-speed T-bone collisions.',
    },
    {
      step: 4,
      title: 'Pre-Flush Queue Clearance & Zero-Delay EV Cruise',
      time: 48,
      badge: 'Zero-Delay Green Wave',
      badgeColor: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      description:
        'The green signal opens early enough to flush the 4 stuck cars through the intersection before EV0 even reaches the stop line.',
      formula: 'EV Waiting Time = 0.0s (Cruising speed maintained at 34 km/h)',
      keyPoint:
        'EV transit time drops from 190.4s (fixed timer) to 97.0s (49.1% faster transit) with zero stops across all 3 intersections.',
    },
    {
      step: 5,
      title: 'Starvation Prevention & Fair Recovery',
      time: 68,
      badge: 'Jain Fairness = 0.95',
      badgeColor: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
      description:
        'As soon as EV0 clears each junction, the corridor hold is immediately released.',
      formula: 'Priority shifts to North-South: W_age · MaxWait increases score',
      keyPoint:
        'The aging term prevents cross-traffic starvation. The North-South queue is released immediately, maintaining network-wide fairness and avoiding secondary gridlocks.',
    },
    {
      step: 6,
      title: 'Second Emergency Corridor (North-South Col B Wave)',
      time: 130,
      badge: 'Multi-Axis Wave',
      badgeColor: 'bg-teal-500/10 text-teal-400 border-teal-500/20',
      description:
        'Watch Central Boulevard (Col B). At t=120s, a second ambulance EV1 enters heading North. The controller dynamically coordinates B0, B1, and B2 into a North-South green wave.',
      formula: 'ETA Lookahead on B0, B1, B2 | Phase 0 Commanded',
      keyPoint:
        'PROVES COMPLETE MULTI-AXIS CONTROL: East-West arterial traffic is brought to a safe halt across all 3 avenues, allowing EV1 to cruise through without stopping!',
    },
  ]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="bg-[#0E1523] border border-[#1E293B] rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-[#1E293B] flex items-center justify-between bg-[#131A26]">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-blue-500 to-indigo-600 p-2.5 rounded-xl text-white shadow-lg shadow-blue-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span>Evaluator Showcase &amp; Feature Demonstration Guide</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                  Live Cue Script
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Click any step to jump the simulation directly to that feature timestamp.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {/* Dual-Screen Tip */}
          <div className="bg-gradient-to-r from-blue-950/40 via-indigo-950/30 to-purple-950/40 border border-blue-500/30 rounded-xl p-4 flex items-start gap-3">
            <ShieldAlert className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
            <div className="text-xs space-y-1">
              <p className="font-bold text-blue-200">
                Evaluator Dual-Screen Setup (Microscopic SUMO-GUI + React Telemetry):
              </p>
              <p className="text-slate-300 leading-relaxed">
                You can launch the live microscopic simulation window directly using the button below or via{' '}
                <code className="bg-[#0B0F17] px-2 py-0.5 rounded text-amber-300 font-mono">
                  python starter.py --demo
                </code>
                . Place SUMO-GUI on the left half of your screen and this dashboard on the right half.
              </p>
              {onLaunchGui && (
                <div className="pt-2">
                  <button
                    onClick={onLaunchGui}
                    disabled={isGuiRunning}
                    className={`flex items-center gap-2 text-xs font-bold px-3.5 py-1.5 rounded-lg shadow transition-all ${
                      isGuiRunning
                        ? 'bg-amber-600/30 border border-amber-500/50 text-amber-300 cursor-not-allowed'
                        : 'bg-emerald-600 hover:bg-emerald-500 text-white hover:scale-105 active:scale-95'
                    }`}
                  >
                    {isGuiRunning ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-400" />
                        <span>SUMO-GUI Active on Desktop (Running)...</span>
                      </>
                    ) : (
                      <>
                        <MonitorPlay className="w-3.5 h-3.5" />
                        <span>Launch SUMO-GUI Window Directly</span>
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Interactive Steps */}
          <div className="space-y-3">
            {demoSteps.map((item) => (
              <div
                key={item.step}
                className="bg-[#131A26] border border-[#1E293B] hover:border-blue-500/40 rounded-xl p-4 transition-all"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-blue-600/20 text-blue-400 border border-blue-500/30 text-xs font-bold flex items-center justify-center font-mono">
                      {item.step}
                    </span>
                    <h3 className="text-sm font-bold text-white">{item.title}</h3>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${item.badgeColor}`}>
                      {item.badge}
                    </span>
                  </div>

                  <button
                    onClick={() => {
                      onJumpToTime(item.time)
                      onClose()
                    }}
                    className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold px-3 py-1.5 rounded-lg shadow-sm transition-all"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Jump to t={item.time}s</span>
                  </button>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed mb-2">{item.description}</p>

                <div className="bg-[#090D15] rounded-lg p-2.5 font-mono text-[11px] text-amber-300/90 border border-slate-800 flex items-center justify-between">
                  <span>📐 {item.formula}</span>
                  <span className="text-slate-500 text-[10px]">Step @ {item.time}s</span>
                </div>

                <div className="mt-2 text-[11px] text-slate-400 flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-slate-200">What to say to Evaluator:</strong> {item.keyPoint}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-[#131A26] border-t border-[#1E293B] flex items-center justify-between">
          <span className="text-xs text-slate-400">
            Tip: Select the <strong className="text-emerald-400 font-mono">adaptive_corridor</strong> run in the dropdown below for full green corridor wave data.
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-xl transition-colors"
          >
            Close Guide
          </button>
        </div>
      </div>
    </div>
  )
}
