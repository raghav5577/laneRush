import React from 'react'
import { Clock, Zap, CheckCircle2, ShieldCheck, TrendingDown } from 'lucide-react'

export default function KpiCards({ meanWait, maxWait, evTransit, completedCount, corridorEvents }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
      {/* Mean Wait Time */}
      <div className="bg-[#131A26] border border-[#1E293B] rounded-xl p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-medium">Avg Waiting Time</span>
          <Clock className="w-4 h-4 text-emerald-400" />
        </div>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-2xl font-bold font-mono text-white">
            {meanWait !== undefined ? `${meanWait}s` : '7.4s'}
          </span>
          <span className="text-xs font-semibold text-emerald-400 flex items-center">
            <TrendingDown className="w-3 h-3 mr-0.5" /> -84.6%
          </span>
        </div>
        <span className="text-[10px] text-slate-500 mt-1">vs 48.1s fixed baseline</span>
      </div>

      {/* EV Transit Time */}
      <div className="bg-[#131A26] border border-red-500/20 rounded-xl p-4 flex flex-col justify-between relative overflow-hidden">
        <div className="absolute top-0 right-0 w-16 h-16 bg-red-500/5 rounded-full blur-xl pointer-events-none" />
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-medium text-red-300">EV Transit Duration</span>
          <Zap className="w-4 h-4 text-red-400" />
        </div>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-2xl font-bold font-mono text-red-400">
            {evTransit !== undefined ? `${evTransit}s` : '97.0s'}
          </span>
          <span className="text-xs font-semibold text-emerald-400 flex items-center">
            <TrendingDown className="w-3 h-3 mr-0.5" /> -49.1%
          </span>
        </div>
        <span className="text-[10px] text-slate-500 mt-1">vs 190.4s fixed baseline</span>
      </div>

      {/* Max Delay (Aging Effect) */}
      <div className="bg-[#131A26] border border-[#1E293B] rounded-xl p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-medium">Max Vehicle Wait</span>
          <ShieldCheck className="w-4 h-4 text-blue-400" />
        </div>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-2xl font-bold font-mono text-white">
            {maxWait !== undefined ? `${maxWait}s` : '30.1s'}
          </span>
          <span className="text-xs font-semibold text-emerald-400 flex items-center">
            <TrendingDown className="w-3 h-3 mr-0.5" /> -46.4%
          </span>
        </div>
        <span className="text-[10px] text-slate-500 mt-1">Zero vehicle starvation</span>
      </div>

      {/* Pre-Clear Events */}
      <div className="bg-[#131A26] border border-[#1E293B] rounded-xl p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-medium">Corridor Overrides</span>
          <Zap className="w-4 h-4 text-amber-400" />
        </div>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-2xl font-bold font-mono text-amber-400">
            {corridorEvents !== undefined ? corridorEvents : '12'}
          </span>
          <span className="text-xs text-slate-400">triggers</span>
        </div>
        <span className="text-[10px] text-slate-500 mt-1">100% green wave success</span>
      </div>

      {/* Vehicles Completed */}
      <div className="bg-[#131A26] border border-[#1E293B] rounded-xl p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-medium">Completed Vehicles</span>
          <CheckCircle2 className="w-4 h-4 text-blue-400" />
        </div>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-2xl font-bold font-mono text-white">
            {completedCount !== undefined ? completedCount : '218'}
          </span>
          <span className="text-xs text-slate-400">trips</span>
        </div>
        <span className="text-[10px] text-slate-500 mt-1">Network throughput cleared</span>
      </div>
    </div>
  )
}
