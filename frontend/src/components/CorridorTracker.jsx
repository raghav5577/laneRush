import React from 'react'
import { ShieldAlert, Navigation, ArrowRight, Gauge } from 'lucide-react'

export default function CorridorTracker({ currentStep }) {
  const t = currentStep?.t || 0

  // Determine active emergency vehicle based on simulation time
  const isEV1Active = t >= 110

  // 1. Calculations for EV0 (Row 1 Eastbound)
  let statusEV0 = 'Inactive'
  let etaA1 = '--'
  let etaB1 = '--'
  let etaC1 = '--'
  let currentLocEV0 = 'Awaiting Dispatch'

  if (t < 40) {
    statusEV0 = 'Scheduled (t=40s)'
    etaA1 = `${(40 - t + 26).toFixed(0)}s`
    etaB1 = `${(40 - t + 52).toFixed(0)}s`
    etaC1 = `${(40 - t + 78).toFixed(0)}s`
    currentLocEV0 = 'Dispatch Queue'
  } else if (t >= 40 && t < 48) {
    statusEV0 = 'Approaching Junction A1'
    etaA1 = `${Math.max(0, 48 - t).toFixed(0)}s`
    etaB1 = `${(56 - t + 26).toFixed(0)}s`
    etaC1 = `${(70 - t + 26).toFixed(0)}s`
    currentLocEV0 = 'Avenue left1A1 (Row 1)'
  } else if (t >= 48 && t < 62) {
    statusEV0 = 'Approaching Junction B1'
    etaA1 = 'Cleared (0s wait)'
    etaB1 = `${Math.max(0, 62 - t).toFixed(0)}s`
    etaC1 = `${(78 - t).toFixed(0)}s`
    currentLocEV0 = 'Avenue A1B1 (Row 1)'
  } else if (t >= 62 && t < 80) {
    statusEV0 = 'Approaching Junction C1'
    etaA1 = 'Cleared (0s wait)'
    etaB1 = 'Cleared (0s wait)'
    etaC1 = `${Math.max(0, 80 - t).toFixed(0)}s`
    currentLocEV0 = 'Avenue B1C1 (Row 1)'
  } else {
    statusEV0 = 'Corridor Transit Complete'
    etaA1 = 'Cleared'
    etaB1 = 'Cleared'
    etaC1 = 'Cleared'
    currentLocEV0 = 'C1right1 (Exit Grid)'
  }

  // 2. Calculations for EV1 (Col B Northbound)
  let statusEV1 = 'Scheduled (t=120s)'
  let etaB0 = '--'
  let etaB1_v1 = '--'
  let etaB2 = '--'
  let currentLocEV1 = 'Boulevard bottom1B0'

  if (t < 120) {
    statusEV1 = 'En Route to Dispatch'
    etaB0 = `${Math.max(0, 120 - t + 10).toFixed(0)}s`
    etaB1_v1 = `${Math.max(0, 120 - t + 28).toFixed(0)}s`
    etaB2 = `${Math.max(0, 120 - t + 48).toFixed(0)}s`
    currentLocEV1 = 'Approaching South Ave'
  } else if (t >= 120 && t < 136) {
    statusEV1 = 'Approaching Junction B0'
    etaB0 = `${Math.max(0, 136 - t).toFixed(0)}s`
    etaB1_v1 = `${Math.max(0, 152 - t).toFixed(0)}s`
    etaB2 = `${Math.max(0, 172 - t).toFixed(0)}s`
    currentLocEV1 = 'Boulevard bottom1B0 (Col B)'
  } else if (t >= 136 && t < 155) {
    statusEV1 = 'Approaching Junction B1'
    etaB0 = 'Cleared (0s wait)'
    etaB1_v1 = `${Math.max(0, 155 - t).toFixed(0)}s`
    etaB2 = `${Math.max(0, 172 - t).toFixed(0)}s`
    currentLocEV1 = 'Boulevard B0B1 (Col B)'
  } else if (t >= 155 && t < 175) {
    statusEV1 = 'Approaching Junction B2'
    etaB0 = 'Cleared (0s wait)'
    etaB1_v1 = 'Cleared (0s wait)'
    etaB2 = `${Math.max(0, 175 - t).toFixed(0)}s`
    currentLocEV1 = 'Boulevard B1B2 (Col B)'
  } else {
    statusEV1 = 'Transit Complete'
    etaB0 = 'Cleared'
    etaB1_v1 = 'Cleared'
    etaB2 = 'Cleared'
    currentLocEV1 = 'B2top1 (Exit Grid)'
  }

  const activeStatus = isEV1Active ? statusEV1 : statusEV0
  const activeLoc = isEV1Active ? currentLocEV1 : currentLocEV0
  const activeVehLabel = isEV1Active
    ? '🚨 Vehicle ID: EV1 (Central Boulevard Express — Col B)'
    : '🚨 Vehicle ID: EV0 (Row 1 Express — Eastbound)'

  const checkpointsEV0 = [
    { id: 'A1', name: 'Junction A1 (West)', eta: etaA1, isGreen: t >= 42 && t <= 52, isPast: t > 52 },
    { id: 'B1', name: 'Junction B1 (Center)', eta: etaB1, isGreen: t >= 52 && t <= 66, isPast: t > 66 },
    { id: 'C1', name: 'Junction C1 (East)', eta: etaC1, isGreen: t >= 66 && t <= 82, isPast: t > 82 },
  ]

  const checkpointsEV1 = [
    { id: 'B0', name: 'Junction B0 (South Ave)', eta: etaB0, isGreen: t >= 122 && t <= 138, isPast: t > 138 },
    { id: 'B1', name: 'Junction B1 (Central Hub)', eta: etaB1_v1, isGreen: t >= 138 && t <= 156, isPast: t > 156 },
    { id: 'B2', name: 'Junction B2 (North Ave)', eta: etaB2, isGreen: t >= 156 && t <= 175, isPast: t > 175 },
  ]

  const activeCheckpoints = isEV1Active ? checkpointsEV1 : checkpointsEV0

  return (
    <div className="bg-[#131A26] border border-[#1E293B] rounded-2xl p-5 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-red-500/20 text-red-400">
              <ShieldAlert className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">EV Green Corridor Tracker</h2>
              <p className="text-xs text-slate-400">Multi-junction lookahead &amp; dynamic queue pre-flush</p>
            </div>
          </div>

          <span
            className={`text-xs font-bold px-2.5 py-1 rounded-full border ${
              (t >= 40 && t <= 80) || (t >= 120 && t <= 175)
                ? 'bg-red-500/20 text-red-400 border-red-500/40 animate-pulse'
                : 'bg-slate-800 text-slate-400 border-slate-700'
            }`}
          >
            {activeStatus}
          </span>
        </div>

        {/* Active EV Telemetry Card */}
        <div className="bg-[#070B11] border border-[#1E293B] rounded-xl p-3.5 mb-4">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="font-bold text-red-400 flex items-center gap-1.5">
              <span>{activeVehLabel}</span>
            </span>
            <span className="text-slate-400 flex items-center gap-1">
              <Gauge className="w-3.5 h-3.5 text-blue-400" />
              <span>Speed: 9.5 m/s (~34 km/h)</span>
            </span>
          </div>

          <div className="flex items-center text-xs text-slate-300 gap-1.5 font-mono">
            <Navigation className="w-3.5 h-3.5 text-emerald-400" />
            <span>Position:</span>
            <span className="text-emerald-400 font-semibold">{activeLoc}</span>
          </div>
        </div>

        {/* Corridor Wave Checkpoints */}
        <div className="space-y-2.5">
          <span className="text-xs font-semibold text-slate-400 tracking-wide uppercase">
            Upstream Signal Pre-Clear Wave ({isEV1Active ? 'Col B Northbound' : 'Row 1 Eastbound'})
          </span>

          {activeCheckpoints.map((cp) => (
            <div
              key={cp.id}
              className={`flex items-center justify-between p-3 rounded-xl border transition-all ${
                cp.isGreen
                  ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-300'
                  : cp.isPast
                  ? 'bg-slate-900/40 border-slate-800 text-slate-500'
                  : 'bg-[#0E1522] border-[#1E293B] text-slate-300'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <span
                  className={`w-6 h-6 rounded-lg text-xs font-bold flex items-center justify-center ${
                    cp.isGreen
                      ? 'bg-emerald-500 text-black font-extrabold shadow-[0_0_10px_rgba(16,185,129,0.5)]'
                      : cp.isPast
                      ? 'bg-slate-800 text-slate-500'
                      : 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                  }`}
                >
                  {cp.id}
                </span>
                <div>
                  <div className="text-xs font-bold">{cp.name}</div>
                  <div className="text-[10px] text-slate-400">
                    {isEV1Active ? 'Phase 0 (North-South Green)' : 'Phase 2 (East-West Green)'}
                  </div>
                </div>
              </div>

              <div className="text-right">
                <div className="text-xs font-mono font-bold">
                  {cp.isGreen ? (
                    <span className="text-emerald-400 flex items-center gap-1">
                      <span>GREEN WAVE</span>
                      <ArrowRight className="w-3 h-3 animate-bounce" />
                    </span>
                  ) : (
                    cp.eta
                  )}
                </div>
                <div className="text-[10px] text-slate-500">
                  {cp.isGreen ? 'Queue Backlog Flushed' : 'Lookahead ≤ 3 TLS'}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Showcase Callout Box */}
      <div className="mt-4 bg-blue-950/20 border border-blue-500/30 rounded-xl p-3 text-xs text-blue-300">
        <span className="font-bold text-white">💡 Multi-Axis Green Waves:</span>{' '}
        {isEV1Active
          ? 'Ambulance EV1 proves North-South corridor adaptability along Col B, immediately bringing East-West cross-traffic to a safe stop!'
          : 'Ambulance EV0 proves East-West corridor adaptability along Row 1, flushing the 4 stuck cars with 0.0s delay!'}
      </div>
    </div>
  )
}
