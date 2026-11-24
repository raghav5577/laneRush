import React from 'react'
import { Play, Pause, RotateCcw, FastForward, FolderOpen } from 'lucide-react'

export default function ControlPanel({
  isPlaying,
  onTogglePlay,
  onReset,
  currentStepIndex,
  totalSteps,
  onSeek,
  playbackSpeed,
  onChangeSpeed,
  runsList,
  selectedRunId,
  onSelectRun,
}) {
  return (
    <div className="bg-[#131A26] border border-[#1E293B] rounded-2xl p-4 flex flex-wrap items-center justify-between gap-4">
      {/* Left: Run Selector */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
          <FolderOpen className="w-4 h-4 text-blue-400" />
          <span>Active Run:</span>
        </div>

        <select
          value={selectedRunId}
          onChange={(e) => onSelectRun(e.target.value)}
          className="bg-[#0B0F17] border border-[#1E293B] text-white text-xs rounded-xl px-3 py-2 outline-none focus:border-blue-500 font-mono"
        >
          {runsList.map((run) => {
            const isCorridor = run.mode === 'adaptive_corridor'
            return (
              <option key={run.id} value={run.id}>
                {isCorridor ? '🚨 [CORRIDOR WAVE] ' : ''}
                {run.id} ({run.mode})
              </option>
            )
          })}
        </select>
      </div>

      {/* Middle: Playback Scrubber & Time */}
      <div className="flex-1 min-w-[280px] max-w-xl flex items-center gap-4">
        <button
          onClick={onTogglePlay}
          className={`p-2.5 rounded-xl font-bold flex items-center justify-center transition-all ${
            isPlaying
              ? 'bg-amber-500 text-black hover:bg-amber-400 shadow-[0_0_15px_rgba(245,158,11,0.4)]'
              : 'bg-blue-600 text-white hover:bg-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.4)]'
          }`}
          title={isPlaying ? 'Pause Simulation' : 'Play Simulation'}
        >
          {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 fill-current" />}
        </button>

        <button
          onClick={onReset}
          className="p-2 rounded-xl bg-[#0B0F17] hover:bg-slate-800 border border-[#1E293B] text-slate-400 hover:text-white"
          title="Reset to Start"
        >
          <RotateCcw className="w-4 h-4" />
        </button>

        {/* Scrubber slider */}
        <div className="flex-1 flex flex-col gap-1">
          <input
            type="range"
            min="0"
            max={Math.max(0, totalSteps - 1)}
            value={currentStepIndex}
            onChange={(e) => onSeek(parseInt(e.target.value, 10))}
            className="w-full accent-blue-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
          />
          <div className="flex justify-between text-[10px] text-slate-500 font-mono">
            <span>Step {currentStepIndex + 1}</span>
            <span>{totalSteps} Total Steps</span>
          </div>
        </div>
      </div>

      {/* Right: Playback Speed Selector */}
      <div className="flex items-center gap-2">
        <FastForward className="w-4 h-4 text-slate-400" />
        <div className="flex items-center bg-[#0B0F17] border border-[#1E293B] rounded-xl p-1 gap-1">
          {[0.5, 1, 2, 5].map((speed) => (
            <button
              key={speed}
              onClick={() => onChangeSpeed(speed)}
              className={`text-xs px-2.5 py-1 rounded-lg font-bold transition-all ${
                playbackSpeed === speed
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {speed}x
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
