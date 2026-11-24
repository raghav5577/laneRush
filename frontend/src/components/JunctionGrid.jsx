import React, { useState } from 'react'

/**
 * Top-down realistic 2D vehicle sprite
 */
function VehicleSprite({ x, y, angle = 0, color = '#38BDF8', isEmergency = false, isBraking = false, label = '' }) {
  return (
    <g transform={`translate(${x}, ${y}) rotate(${angle})`} className="transition-transform duration-200">
      {/* Emergency Siren Aura */}
      {isEmergency && (
        <circle cx="0" cy="0" r="22" fill="#EF4444" fillOpacity="0.3" className="animate-ping" />
      )}

      {/* Vehicle Shadow */}
      <rect
        x="-10"
        y="-5.5"
        width="20"
        height="11"
        rx="3.5"
        fill="#000000"
        fillOpacity="0.45"
        transform="translate(1.5, 2)"
      />

      {/* Main Vehicle Chassis */}
      <rect
        x="-10"
        y="-5.5"
        width="20"
        height="11"
        rx="3.5"
        fill={isEmergency ? '#EF4444' : color}
        stroke={isEmergency ? '#FFFFFF' : '#0F172A'}
        strokeWidth={isEmergency ? '1.2' : '0.8'}
      />

      {/* Roof Cabin / Glass */}
      <rect
        x="-4"
        y="-4"
        width="9"
        height="8"
        rx="2"
        fill="#0F172A"
        fillOpacity="0.85"
      />
      {/* Windshield glare */}
      <rect x="2" y="-3.5" width="2" height="7" rx="1" fill="#94A3B8" fillOpacity="0.6" />

      {/* Headlights (Front is +X direction) */}
      <circle cx="9.5" cy="-3.5" r="1.4" fill="#FEF08A" />
      <circle cx="9.5" cy="3.5" r="1.4" fill="#FEF08A" />
      {/* Headlight beam */}
      <polygon
        points="10,-4 22,-8 22,8 10,4"
        fill="#FEF08A"
        fillOpacity={isEmergency ? '0.25' : '0.12'}
      />

      {/* Taillights (Rear is -X direction) */}
      <circle
        cx="-9.5"
        cy="-3.5"
        r="1.3"
        fill={isBraking ? '#FF2E4D' : '#991B1B'}
        filter={isBraking ? 'url(#brake-glow)' : undefined}
      />
      <circle
        cx="-9.5"
        cy="3.5"
        r="1.3"
        fill={isBraking ? '#FF2E4D' : '#991B1B'}
        filter={isBraking ? 'url(#brake-glow)' : undefined}
      />

      {/* Emergency Roof Strobe / Cross */}
      {isEmergency ? (
        <g>
          {/* Ambulance Cross */}
          <rect x="-2" y="-4" width="4" height="8" fill="#FFFFFF" rx="0.5" />
          <rect x="-4" y="-2" width="8" height="4" fill="#FFFFFF" rx="0.5" />
          <rect x="-1" y="-3" width="2" height="6" fill="#EF4444" />
          <rect x="-3" y="-1" width="6" height="2" fill="#EF4444" />
          {/* Dual Strobe Lights */}
          <circle cx="-1" cy="0" r="2.2" fill="#3B82F6" className="animate-pulse" />
          <circle cx="1" cy="0" r="2.2" fill="#EF4444" className="animate-pulse" />
        </g>
      ) : null}

      {/* Floating Vehicle Label */}
      {label && (
        <g transform={`rotate(${-angle}) translate(0, -14)`}>
          <rect x="-22" y="-7" width="44" height="12" rx="3" fill="rgba(15, 23, 42, 0.85)" stroke="#334155" strokeWidth="0.5" />
          <text x="0" y="2" textAnchor="middle" fill="#E2E8F0" fontSize="7" fontFamily="sans-serif" fontWeight="bold">
            {label}
          </text>
        </g>
      )}
    </g>
  )
}

export default function JunctionGrid({ network, currentStep, selectedJunction, onSelectJunction }) {
  const [showRealVehicles, setShowRealVehicles] = useState(true)

  if (!network || !network.junctions) {
    return (
      <div className="bg-[#131A26] border border-[#1E293B] rounded-2xl p-8 flex items-center justify-center text-slate-500">
        Loading network topology...
      </div>
    )
  }

  const junctions = network.junctions
  const junctionsList = Object.values(junctions)
  const currentDecisions = currentStep?.junctions || {}
  const t = currentStep?.t || 0

  // -------------------------------------------------------------------------
  // Realistic Microscopic Vehicle Trajectory Engine
  // -------------------------------------------------------------------------

  // 1. Emergency Vehicles (EV0 along Row 1, EV1 along Col B)
  // EV0: Spawns at t=40s, arrives A1 at t=48s, B1 at t=65s, C1 at t=82s, exits at t=95s
  // EV1: Spawns at t=120s, arrives B0 at t=128s, B1 at t=148s, B2 at t=168s, exits at t=185s
  let evCar = null
  let activeCorridorAxis = null // 'row1' or 'colB'

  if (t >= 40 && t <= 98) {
    const progress = Math.min(1, Math.max(0, (t - 40) / 52))
    const evX = 35 + progress * 620
    evCar = {
      x: evX,
      y: 280,
      angle: 0,
      speed: '9.5 m/s (34 km/h)',
      label: '🚨 AMBULANCE EV0 (Row 1)',
    }
    activeCorridorAxis = 'row1'
  } else if (t >= 120 && t <= 185) {
    const progress = Math.min(1, Math.max(0, (t - 120) / 58))
    const evY = 510 - progress * 460
    evCar = {
      x: 350,
      y: evY,
      angle: 270,
      speed: '9.5 m/s (34 km/h)',
      label: '🚨 AMBULANCE EV1 (Col B)',
    }
    activeCorridorAxis = 'colB'
  }

  // 2. The 4 Passenger Cars ahead of EV0 on Row 1 (The Pre-Flush Bottleneck)
  // At t < 42s, they are stuck in a queue at the red light at Junction A1 (x=120)
  // At t >= 42s, the corridor turns green! They accelerate and drive through A1, B1, C1
  const corridorCars = []
  const carColors = ['#F8FAFC', '#38BDF8', '#F59E0B', '#94A3B8']

  for (let i = 0; i < 4; i++) {
    const stopX = 96 - i * 18 // Stopped before A1 stop line (x=120)
    let carX = stopX
    let isBraking = true

    if (t >= 42) {
      // Accelerate forward after green light at t=42s
      isBraking = false
      const timeMoving = Math.max(0, t - 42 - i * 0.8)
      carX = stopX + timeMoving * 14.5
    }

    if (carX < 690) {
      corridorCars.push({
        id: `corridor-car-${i + 1}`,
        x: carX,
        y: 280,
        angle: 0,
        color: carColors[i],
        isBraking: isBraking,
        label: t < 42 ? `Car ${i + 1} (Queued)` : `Car ${i + 1}`,
      })
    }
  }

  // 3. Cross-Traffic Vehicles on Boulevard A (Col A: x=120, Southbound)
  // At t < 40: Moves south freely
  // At 40 <= t <= 64: Junction A1 turns Red for NS! Vehicles must brake and halt north of A1 (y=280)
  // At t > 64: EV0 cleared! NS turns Green again, vehicles resume moving south
  const colAVehicles = []
  if (t < 40) {
    // Normal flowing car
    const carY = ((t * 12) % 480) + 40
    colAVehicles.push({ x: 120, y: carY, angle: 90, color: '#38BDF8', isBraking: false, label: 'Cross-Traffic' })
  } else if (t >= 40 && t <= 64) {
    // Halted cars waiting for corridor to clear!
    colAVehicles.push({
      x: 120,
      y: 250,
      angle: 90,
      color: '#EF4444',
      isBraking: true,
      label: 'Halted (Red Light)',
    })
    colAVehicles.push({
      x: 120,
      y: 228,
      angle: 90,
      color: '#CBD5E1',
      isBraking: true,
      label: 'Queue #2',
    })
    colAVehicles.push({
      x: 120,
      y: 310,
      angle: 270,
      color: '#F59E0B',
      isBraking: true,
      label: 'Northbound Halted',
    })
  } else {
    // Green light resumed: Halted cars driving forward
    const resumedY = 250 + (t - 64) * 14
    if (resumedY < 530) {
      colAVehicles.push({ x: 120, y: resumedY, angle: 90, color: '#38BDF8', isBraking: false, label: 'Resumed NS' })
    }
  }

  // 4. Cross-Traffic on Boulevard B (Col B: x=350)
  const colBVehicles = []
  if (t >= 52 && t <= 75) {
    // Halted before B1 while EV approaches
    colBVehicles.push({ x: 350, y: 250, angle: 90, color: '#E2E8F0', isBraking: true, label: 'Halted B1' })
  } else {
    const carY = (((t + 10) * 11) % 460) + 50
    colBVehicles.push({ x: 350, y: carY, angle: 90, color: '#94A3B8', isBraking: false, label: '' })
  }

  // 5. Cross-Traffic on Boulevard C (Col C: x=580)
  const colCVehicles = []
  if (t >= 68 && t <= 88) {
    colCVehicles.push({ x: 580, y: 250, angle: 90, color: '#CBD5E1', isBraking: true, label: 'Halted C1' })
  } else {
    const carY = (((t + 25) * 10) % 460) + 50
    colCVehicles.push({ x: 580, y: carY, angle: 90, color: '#38BDF8', isBraking: false, label: '' })
  }

  // 6. Ambient Vehicles on Outer Avenues (Row 0 y=440 and Row 2 y=120)
  const ambientCars = [
    { x: ((t * 11 + 60) % 640) + 30, y: 120, angle: 0, color: '#E2E8F0', isBraking: false, label: '' },
    { x: 670 - ((t * 10 + 120) % 640), y: 440, angle: 180, color: '#38BDF8', isBraking: false, label: '' },
  ]

  return (
    <div className="bg-[#131A26] border border-[#1E293B] rounded-2xl p-5 flex flex-col">
      {/* Top Header & Controls */}
      <div className="flex flex-wrap items-center justify-between mb-4 gap-3">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <span>3×3 Signalized Network Map</span>
            <span className="text-xs font-mono font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
              Microscopic Vehicle View
            </span>
          </h2>
          <p className="text-xs text-slate-400">
            Real passenger cars, queue formation, dynamic signal switching &amp; emergency green wave
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-4 text-xs font-medium">
          {/* View Toggle */}
          <button
            onClick={() => setShowRealVehicles(!showRealVehicles)}
            className={`px-2.5 py-1 rounded-lg border text-xs font-semibold transition-all ${
              showRealVehicles
                ? 'bg-blue-600/20 border-blue-500/40 text-blue-300'
                : 'bg-slate-800 border-slate-700 text-slate-400'
            }`}
          >
            {showRealVehicles ? '🚘 Realistic Cars: ON' : '⚫ Simple Dots'}
          </button>

          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
            <span className="text-slate-300">Green</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.8)]" />
            <span className="text-slate-300">Yellow</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]" />
            <span className="text-slate-300">Red (Queued)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-red-600 border border-white animate-pulse" />
            <span className="text-red-400 font-bold">Ambulance EV0</span>
          </div>
        </div>
      </div>

      {/* SVG Canvas Map */}
      <div className="relative bg-[#070B11] border border-[#1E293B] rounded-xl p-4 flex items-center justify-center overflow-hidden">
        <svg viewBox="0 0 700 560" className="w-full max-w-[700px] h-auto select-none">
          <defs>
            <pattern id="grid-pattern" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1E293B" strokeWidth="0.5" strokeOpacity="0.4" />
            </pattern>
            <filter id="siren-glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="brake-glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="green-glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Background Grid */}
          <rect width="100%" height="100%" fill="url(#grid-pattern)" />

          {/* Horizontal Roads (Avenues) */}
          {[120, 280, 440].map((y, idx) => (
            <g key={`row-${idx}`}>
              {/* Asphalt Road Surface */}
              <line x1="20" y1={y} x2="680" y2={y} stroke="#1A2234" strokeWidth="36" strokeLinecap="round" />
              {/* Road Shoulders / Curbs */}
              <line x1="20" y1={y - 18} x2="680" y2={y - 18} stroke="#334155" strokeWidth="1" />
              <line x1="20" y1={y + 18} x2="680" y2={y + 18} stroke="#334155" strokeWidth="1" />
              {/* Dashed Center Dividing Line */}
              <line x1="20" y1={y} x2="680" y2={y} stroke="#475569" strokeWidth="1.5" strokeDasharray="8,8" />
              <text x="25" y={y - 22} fill="#64748B" fontSize="9" fontFamily="sans-serif" fontWeight="bold">
                {idx === 1 ? 'ROW 1 (MAIN GREEN CORRIDOR — EASTBOUND)' : `ROW ${idx === 0 ? '2 (NORTH AVE)' : '0 (SOUTH AVE)'}`}
              </text>
            </g>
          ))}

          {/* Vertical Roads (Boulevards) */}
          {[120, 350, 580].map((x, idx) => (
            <g key={`col-${idx}`}>
              {/* Asphalt Road Surface */}
              <line x1={x} y1="30" x2={x} y2="530" stroke="#1A2234" strokeWidth="36" strokeLinecap="round" />
              {/* Curbs */}
              <line x1={x - 18} y1="30" x2={x - 18} y2="530" stroke="#334155" strokeWidth="1" />
              <line x1={x + 18} y1="30" x2={x + 18} y2="530" stroke="#334155" strokeWidth="1" />
              {/* Dashed Center Dividing Line */}
              <line x1={x} y1="30" x2={x} y2="530" stroke="#475569" strokeWidth="1.5" strokeDasharray="8,8" />
              <text x={x - 24} y="45" fill="#64748B" fontSize="9" fontFamily="sans-serif" fontWeight="bold">
                {`COL ${String.fromCharCode(65 + idx)}`}
              </text>
            </g>
          ))}

          {/* Green Corridor Wave Glow along Row 1 or Col B when EV is in network */}
          {activeCorridorAxis === 'row1' && (
            <line
              x1="20"
              y1="280"
              x2="680"
              y2="280"
              stroke="#10B981"
              strokeWidth="10"
              strokeOpacity="0.35"
              className="animate-wave"
            />
          )}
          {activeCorridorAxis === 'colB' && (
            <line
              x1="350"
              y1="30"
              x2="350"
              y2="530"
              stroke="#10B981"
              strokeWidth="10"
              strokeOpacity="0.35"
              className="animate-wave"
            />
          )}

          {/* Stop Lines & Crosswalks at all 9 intersections */}
          {junctionsList.map((junc) => {
            const xMap = { 0: 120, 1: 350, 2: 580 }
            const yMap = { 0: 440, 1: 280, 2: 120 }
            const cx = xMap[junc.col]
            const cy = yMap[junc.row]

            return (
              <g key={`stoplines-${junc.id}`}>
                {/* West stop line */}
                <line x1={cx - 26} y1={cy - 16} x2={cx - 26} y2={cy + 16} stroke="#FFFFFF" strokeWidth="2.5" strokeOpacity="0.75" />
                {/* East stop line */}
                <line x1={cx + 26} y1={cy - 16} x2={cx + 26} y2={cy + 16} stroke="#FFFFFF" strokeWidth="2.5" strokeOpacity="0.75" />
                {/* North stop line */}
                <line x1={cx - 16} y1={cy - 26} x2={cx + 16} y2={cy - 26} stroke="#FFFFFF" strokeWidth="2.5" strokeOpacity="0.75" />
                {/* South stop line */}
                <line x1={cx - 16} y1={cy + 26} x2={cx + 16} y2={cy + 26} stroke="#FFFFFF" strokeWidth="2.5" strokeOpacity="0.75" />
              </g>
            )
          })}

          {/* Render All 9 Junctions, Signals, and Physical Intersection Boxes */}
          {junctionsList.map((junc) => {
            const xMap = { 0: 120, 1: 350, 2: 580 }
            const yMap = { 0: 440, 1: 280, 2: 120 }
            const cx = xMap[junc.col]
            const cy = yMap[junc.row]

            const decision = currentDecisions[junc.id] || {}
            const reason = decision.reason || 'stay'
            const targetPhase = decision.target_phase
            const scores = decision.scores || {}
            const scoreNS = scores.phase_0 || 0
            const scoreEW = scores.phase_2 || 0

            const isCorridor = reason === 'corridor' || reason === 'corridor_hold'
            const isSelected = selectedJunction === junc.id

            // Determine Phase Colors (Phase 0 = NS, Phase 2 = EW)
            let nsColor = '#EF4444' // Red
            let ewColor = '#EF4444' // Red
            let activeDirection = 'NS'

            if (isCorridor) {
              ewColor = '#10B981' // Green
              nsColor = '#EF4444' // Red
              activeDirection = 'EW'
            } else if (targetPhase === 2) {
              ewColor = '#F59E0B' // Yellow switching to EW
              nsColor = '#EF4444'
            } else if (targetPhase === 0) {
              nsColor = '#F59E0B' // Yellow switching to NS
              ewColor = '#EF4444'
            } else if (scoreEW > scoreNS && scoreEW > 4.0) {
              ewColor = '#10B981'
              nsColor = '#EF4444'
              activeDirection = 'EW'
            } else {
              nsColor = '#10B981'
              ewColor = '#EF4444'
              activeDirection = 'NS'
            }

            return (
              <g
                key={junc.id}
                onClick={() => onSelectJunction && onSelectJunction(junc.id)}
                className="cursor-pointer transition-transform hover:scale-105"
              >
                {/* Intersection Area Box */}
                <rect
                  x={cx - 24}
                  y={cy - 24}
                  width="48"
                  height="48"
                  rx="8"
                  fill="#131A26"
                  stroke={isSelected ? '#3B82F6' : isCorridor ? '#EF4444' : '#334155'}
                  strokeWidth={isSelected || isCorridor ? '2.5' : '1.5'}
                  filter={isCorridor ? 'url(#green-glow)' : undefined}
                />

                {/* Junction ID Label */}
                <text
                  x={cx}
                  y={cy - 4}
                  textAnchor="middle"
                  fill="#FFFFFF"
                  fontSize="12"
                  fontFamily="sans-serif"
                  fontWeight="bold"
                >
                  {junc.id}
                </text>

                {/* Live Rush Score Text inside intersection */}
                <text
                  x={cx}
                  y={cy + 10}
                  textAnchor="middle"
                  fill={activeDirection === 'EW' ? '#60A5FA' : '#34D399'}
                  fontSize="8"
                  fontFamily="monospace"
                  fontWeight="bold"
                >
                  {activeDirection === 'EW' ? `EW:${scoreEW.toFixed(0)}` : `NS:${scoreNS.toFixed(0)}`}
                </text>

                {/* North-South Traffic Signal Heads */}
                <circle cx={cx} cy={cy - 18} r="3.5" fill={nsColor} />
                <circle cx={cx} cy={cy + 18} r="3.5" fill={nsColor} />

                {/* East-West Traffic Signal Heads */}
                <circle cx={cx - 18} cy={cy} r="3.5" fill={ewColor} />
                <circle cx={cx + 18} cy={cy} r="3.5" fill={ewColor} />

                {/* Reason Status Badge below junction */}
                <rect
                  x={cx - 30}
                  y={cy + 28}
                  width="60"
                  height="15"
                  rx="4"
                  fill={isCorridor ? 'rgba(239, 68, 68, 0.25)' : 'rgba(15, 23, 42, 0.9)'}
                  stroke={isCorridor ? '#EF4444' : '#1E293B'}
                  strokeWidth="1"
                />
                <text
                  x={cx}
                  y={cy + 39}
                  textAnchor="middle"
                  fill={isCorridor ? '#EF4444' : '#94A3B8'}
                  fontSize="7.5"
                  fontFamily="monospace"
                  fontWeight="bold"
                >
                  {isCorridor ? '🚨PRE-CLEAR' : reason.toUpperCase()}
                </text>
              </g>
            )
          })}

          {/* ----------------------------------------------------------------- */}
          {/* REALISTIC MOVING PASSENGER VEHICLES & EMERGENCY VEHICLE           */}
          {/* ----------------------------------------------------------------- */}

          {showRealVehicles && (
            <g id="microscopic-vehicles-layer">
              {/* 1. Ambient Vehicles on Outer Avenues */}
              {ambientCars.map((car, idx) => (
                <VehicleSprite key={`amb-${idx}`} {...car} />
              ))}

              {/* 2. Cross-Traffic Vehicles on Col A, B, C */}
              {colAVehicles.map((car, idx) => (
                <VehicleSprite key={`colA-${idx}`} {...car} />
              ))}
              {colBVehicles.map((car, idx) => (
                <VehicleSprite key={`colB-${idx}`} {...car} />
              ))}
              {colCVehicles.map((car, idx) => (
                <VehicleSprite key={`colC-${idx}`} {...car} />
              ))}

              {/* 3. The 4 Corridor Passenger Cars (Flushed on Green ahead of EV0) */}
              {corridorCars.map((car) => (
                <VehicleSprite key={car.id} {...car} />
              ))}

              {/* Context Callout Box for the 4 Stuck Cars before green */}
              {t < 42 && (
                <g>
                  <rect
                    x="25"
                    y="246"
                    width="100"
                    height="18"
                    rx="4"
                    fill="rgba(239, 68, 68, 0.25)"
                    stroke="#EF4444"
                    strokeWidth="1"
                  />
                  <text
                    x="75"
                    y="258"
                    textAnchor="middle"
                    fill="#EF4444"
                    fontSize="7.5"
                    fontFamily="sans-serif"
                    fontWeight="bold"
                  >
                    4 CARS STUCK AT RED (QUEUED)
                  </text>
                </g>
              )}

              {/* Context Callout Box for Flushed Cars after green */}
              {t >= 42 && t <= 58 && (
                <g>
                  <rect
                    x="135"
                    y="246"
                    width="115"
                    height="18"
                    rx="4"
                    fill="rgba(16, 185, 129, 0.25)"
                    stroke="#10B981"
                    strokeWidth="1"
                  />
                  <text
                    x="192"
                    y="258"
                    textAnchor="middle"
                    fill="#10B981"
                    fontSize="7.5"
                    fontFamily="sans-serif"
                    fontWeight="bold"
                  >
                    QUEUE FLUSHED ON GREEN WAVE
                  </text>
                </g>
              )}

              {/* 4. Emergency Vehicle EV0 with Animated Siren and Headlight Beam */}
              {evCar && (
                <VehicleSprite
                  x={evCar.x}
                  y={evCar.y}
                  angle={evCar.angle}
                  color="#EF4444"
                  isEmergency={true}
                  isBraking={false}
                  label="🚨 AMBULANCE EV0 (34 km/h)"
                />
              )}
            </g>
          )}
        </svg>
      </div>
    </div>
  )
}
