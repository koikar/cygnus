import { useRef, useEffect, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Grid, Stars } from '@react-three/drei';
import useAppStore from '../store/useAppStore.js';

const DEG = Math.PI / 180;

function lerp(a, b, t) {
  return a + (b - a) * t;
}

// Articulated robot arm built from Three.js primitives
function RobotArm({ targetJoints, scene }) {
  const display = useRef({
    shoulder_pan: 0, shoulder_lift: 0, elbow_flex: 0,
    wrist_flex: 0, wrist_roll: 0, gripper: 0,
  });

  const shoulderPanRef = useRef();
  const shoulderLiftRef = useRef();
  const elbowFlexRef = useRef();
  const wristFlexRef = useRef();
  const wristRollRef = useRef();
  const fingerLRef = useRef();
  const fingerRRef = useRef();

  useFrame(() => {
    const t = 0.07;
    const d = display.current;
    const tgt = targetJoints;
    d.shoulder_pan = lerp(d.shoulder_pan, tgt.shoulder_pan, t);
    d.shoulder_lift = lerp(d.shoulder_lift, tgt.shoulder_lift, t);
    d.elbow_flex = lerp(d.elbow_flex, tgt.elbow_flex, t);
    d.wrist_flex = lerp(d.wrist_flex, tgt.wrist_flex, t);
    d.wrist_roll = lerp(d.wrist_roll, tgt.wrist_roll, t);
    d.gripper = lerp(d.gripper, tgt.gripper, t);

    if (shoulderPanRef.current) shoulderPanRef.current.rotation.y = d.shoulder_pan * DEG;
    if (shoulderLiftRef.current) shoulderLiftRef.current.rotation.x = d.shoulder_lift * DEG;
    if (elbowFlexRef.current) elbowFlexRef.current.rotation.x = d.elbow_flex * DEG;
    if (wristFlexRef.current) wristFlexRef.current.rotation.x = d.wrist_flex * DEG;
    if (wristRollRef.current) wristRollRef.current.rotation.z = d.wrist_roll * DEG;

    // When holding, close fingers tightly around the cube; otherwise open fully
    const targetSpread = scene.holding ? 0.028 : 0.025 + (d.gripper / 40) * 0.028;
    if (fingerLRef.current) fingerLRef.current.position.x = -targetSpread;
    if (fingerRRef.current) fingerRRef.current.position.x = targetSpread;
  });

  // Vibrant neon-blue palette that pops against dark navy background
  const metal = { metalness: 0.55, roughness: 0.18 };
  const joint = {
    color: '#00cfff', emissive: '#0099cc', emissiveIntensity: 0.55, ...metal,
  };
  const link = {
    color: '#0c2e5e', emissive: '#051830', emissiveIntensity: 0.2, ...metal,
  };
  const wristJoint = {
    color: '#ffe040', emissive: '#cc9000', emissiveIntensity: 0.6, ...metal,
  };
  const fingerMat = {
    color: '#38d8f0', emissive: '#1a8fa8', emissiveIntensity: 0.35, ...metal,
  };

  return (
    <group position={[0, 0.1, 0]}>
      {/* Base plate */}
      <mesh position={[0, 0.028, 0]}>
        <cylinderGeometry args={[0.1, 0.13, 0.056, 24]} />
        <meshStandardMaterial color="#08111f" emissive="#00cfff" emissiveIntensity={0.08} {...metal} />
      </mesh>
      {/* Base ring glow */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.057, 0]}>
        <ringGeometry args={[0.1, 0.115, 32]} />
        <meshStandardMaterial color="#00cfff" emissive="#00cfff" emissiveIntensity={1} transparent opacity={0.55} />
      </mesh>

      {/* Shoulder pan — rotates Y */}
      <group ref={shoulderPanRef}>
        {/* Shoulder joint sphere */}
        <mesh position={[0, 0.095, 0]}>
          <sphereGeometry args={[0.062, 24, 24]} />
          <meshStandardMaterial {...joint} />
        </mesh>

        {/* Shoulder lift — rotates X */}
        <group ref={shoulderLiftRef} position={[0, 0.095, 0]}>
          {/* Upper arm — section height 0.62 */}
          <mesh position={[0, 0.31, 0]}>
            <boxGeometry args={[0.068, 0.62, 0.068]} />
            <meshStandardMaterial {...link} />
          </mesh>
          {/* Upper arm accent stripe */}
          <mesh position={[0.036, 0.31, 0]}>
            <boxGeometry args={[0.006, 0.61, 0.06]} />
            <meshStandardMaterial color="#00e8ff" emissive="#00e8ff" emissiveIntensity={0.9} />
          </mesh>
          {/* Second stripe opposite side */}
          <mesh position={[-0.036, 0.31, 0]}>
            <boxGeometry args={[0.004, 0.61, 0.06]} />
            <meshStandardMaterial color="#00b4e0" emissive="#00b4e0" emissiveIntensity={0.5} />
          </mesh>

          {/* Elbow joint — positioned at end of extended upper arm */}
          <group ref={elbowFlexRef} position={[0, 0.64, 0]}>
            <mesh>
              <sphereGeometry args={[0.054, 24, 24]} />
              <meshStandardMaterial {...joint} />
            </mesh>

            {/* Forearm — section height 0.50 */}
            <mesh position={[0, 0.255, 0]}>
              <boxGeometry args={[0.056, 0.50, 0.056]} />
              <meshStandardMaterial {...link} />
            </mesh>
            <mesh position={[0.03, 0.255, 0]}>
              <boxGeometry args={[0.005, 0.49, 0.049]} />
              <meshStandardMaterial color="#00e8ff" emissive="#00e8ff" emissiveIntensity={0.9} />
            </mesh>

            {/* Wrist flex — positioned at end of extended forearm */}
            <group ref={wristFlexRef} position={[0, 0.52, 0]}>
              {/* Wrist roll — rotates Z */}
              <group ref={wristRollRef}>
                {/* Wrist joint */}
                <mesh>
                  <sphereGeometry args={[0.038, 20, 20]} />
                  <meshStandardMaterial {...wristJoint} />
                </mesh>

                {/* Palm */}
                <mesh position={[0, 0.052, 0]}>
                  <boxGeometry args={[0.078, 0.078, 0.038]} />
                  <meshStandardMaterial color="#0c2e5e" emissive="#00cfff" emissiveIntensity={0.15} {...metal} />
                </mesh>

                {/* Finger left */}
                <mesh ref={fingerLRef} position={[-0.025, 0.108, 0]}>
                  <boxGeometry args={[0.02, 0.065, 0.024]} />
                  <meshStandardMaterial {...fingerMat} />
                </mesh>
                {/* Finger right */}
                <mesh ref={fingerRRef} position={[0.025, 0.108, 0]}>
                  <boxGeometry args={[0.02, 0.065, 0.024]} />
                  <meshStandardMaterial {...fingerMat} />
                </mesh>

                {/* Held cube — only visible when gripper is holding */}
                {scene.holding && (
                  <mesh position={[0, 0.108, 0]}>
                    <boxGeometry args={[0.038, 0.038, 0.038]} />
                    <meshStandardMaterial
                      color="#00d68f"
                      emissive="#00d68f"
                      emissiveIntensity={0.8}
                      metalness={0.2}
                      roughness={0.4}
                    />
                  </mesh>
                )}
              </group>
            </group>
          </group>
        </group>
      </group>
    </group>
  );
}

// Zone positions in 3D space
const ZONE_POS = {
  A: [-0.28, 0.115, 0.2],
  B: [0.28, 0.115, 0.2],
  C: [0.45, 0.115, 0.05],
  BIN: [0.38, 0.115, -0.2],
};

function SceneObjects({ scene }) {
  const cubePos = scene.cube_in_bin
    ? ZONE_POS.BIN
    : (ZONE_POS[scene.cube_zone] || ZONE_POS.A);

  const cubeColor = scene.cube_in_bin ? '#00d68f' : (scene.holding ? '#00d68f' : '#ef4444');

  return (
    <>
      {/* Table surface */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.1, 0]} receiveShadow>
        <planeGeometry args={[2.4, 2.4]} />
        <meshStandardMaterial color="#0a1628" metalness={0.1} roughness={0.9} />
      </mesh>

      {/* Table border glow */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.101, 0]}>
        <ringGeometry args={[0.97, 1.0, 48]} />
        <meshStandardMaterial color="#2d8cf0" transparent opacity={0.15} />
      </mesh>

      {/* Safe workspace halo */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.102, 0]}>
        <ringGeometry args={[0.52, 0.56, 48]} />
        <meshStandardMaterial color="#00d68f" transparent opacity={0.18} />
      </mesh>

      {/* Zone A marker */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[ZONE_POS.A[0], 0.102, ZONE_POS.A[2]]}>
        <ringGeometry args={[0.055, 0.07, 20]} />
        <meshStandardMaterial color="#3b82f6" transparent opacity={0.6} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[ZONE_POS.A[0], 0.1025, ZONE_POS.A[2]]}>
        <circleGeometry args={[0.055, 20]} />
        <meshStandardMaterial color="#3b82f6" transparent opacity={0.1} />
      </mesh>

      {/* Zone B marker */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[ZONE_POS.B[0], 0.102, ZONE_POS.B[2]]}>
        <ringGeometry args={[0.055, 0.07, 20]} />
        <meshStandardMaterial color="#8b5cf6" transparent opacity={0.6} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[ZONE_POS.B[0], 0.1025, ZONE_POS.B[2]]}>
        <circleGeometry args={[0.055, 20]} />
        <meshStandardMaterial color="#8b5cf6" transparent opacity={0.1} />
      </mesh>

      {/* Cube on ground — hidden while arm is holding it (it moves with the gripper instead) */}
      {!scene.holding && (
        <mesh position={cubePos} castShadow>
          <boxGeometry args={[0.055, 0.055, 0.055]} />
          <meshStandardMaterial
            color={cubeColor}
            emissive={cubeColor}
            emissiveIntensity={scene.cube_in_bin ? 0.6 : 0.3}
            metalness={0.3}
            roughness={0.4}
          />
        </mesh>
      )}

      {/* Bin — wireframe box */}
      <mesh position={[ZONE_POS.BIN[0], 0.14, ZONE_POS.BIN[2]]}>
        <boxGeometry args={[0.14, 0.08, 0.14]} />
        <meshStandardMaterial color="#00d68f" transparent opacity={0.08} />
      </mesh>
      <mesh position={[ZONE_POS.BIN[0], 0.14, ZONE_POS.BIN[2]]}>
        <boxGeometry args={[0.14, 0.08, 0.14]} />
        <meshStandardMaterial color="#00d68f" transparent opacity={0.5} wireframe />
      </mesh>

      {/* Zone labels (planes with glowing dots) */}
      <pointLight position={[ZONE_POS.A[0], 0.5, ZONE_POS.A[2]]} intensity={0.3} color="#3b82f6" distance={0.8} />
      <pointLight position={[ZONE_POS.B[0], 0.5, ZONE_POS.B[2]]} intensity={0.3} color="#8b5cf6" distance={0.8} />
      <pointLight position={[ZONE_POS.BIN[0], 0.5, ZONE_POS.BIN[2]]} intensity={0.4} color="#00d68f" distance={0.8} />
    </>
  );
}

function Lighting() {
  return (
    <>
      <ambientLight intensity={0.22} />
      <directionalLight position={[3, 7, 4]} intensity={1.1} castShadow
        shadow-mapSize-width={1024} shadow-mapSize-height={1024} />
      {/* Cyan fill from above-front */}
      <pointLight position={[0.4, 1.8, 0.8]} intensity={1.0} color="#00cfff" distance={3.5} />
      {/* Blue-purple rim from behind */}
      <pointLight position={[-0.8, 1.2, -0.6]} intensity={0.6} color="#5080ff" distance={3} />
      {/* Warm base accent */}
      <pointLight position={[0, 0.3, 0.4]} intensity={0.35} color="#ffe040" distance={1.5} />
    </>
  );
}

function StatusChip({ label, value, color, pulse = false }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6,
      padding: '4px 10px',
      background: 'rgba(6,11,24,0.75)',
      borderRadius: 20,
      border: `1px solid ${color}55`,
      backdropFilter: 'blur(6px)',
    }}>
      {pulse && (
        <div style={{
          width: 6, height: 6, borderRadius: '50%',
          background: color,
          animation: 'pulse 1.2s ease-in-out infinite',
          flexShrink: 0,
        }} />
      )}
      <span style={{ fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.08em' }}>{label}</span>
      <span style={{ fontSize: 10, fontWeight: 700, color }}>{value}</span>
    </div>
  );
}

function FallbackRobot() {
  return (
    <div style={{
      width: '100%', height: '100%',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'var(--bg-card)', borderRadius: 'var(--radius)',
      color: 'var(--text-secondary)', fontSize: 13, flexDirection: 'column', gap: 12,
    }}>
      <svg width="60" height="80" viewBox="0 0 60 80" fill="none" opacity={0.5}>
        <rect x="20" y="0" width="20" height="15" rx="3" fill="#2d8cf0" />
        <rect x="22" y="15" width="16" height="25" rx="2" fill="#1e3a5f" />
        <rect x="22" y="40" width="16" height="20" rx="2" fill="#1e3a5f" />
        <rect x="10" y="16" width="10" height="18" rx="2" fill="#334155" />
        <rect x="40" y="16" width="10" height="18" rx="2" fill="#334155" />
        <rect x="22" y="60" width="6" height="20" rx="2" fill="#334155" />
        <rect x="32" y="60" width="6" height="20" rx="2" fill="#334155" />
      </svg>
      <span>WebGL unavailable — simplified view</span>
    </div>
  );
}

export default function Robot3D() {
  const joints = useAppStore(s => s.joints);
  const scene = useAppStore(s => s.scene);
  const connectionMode = useAppStore(s => s.connectionMode);
  const backendOnline = useAppStore(s => s.backendOnline);

  const isLive = connectionMode === 'live' && backendOnline;

  return (
    <div style={{ width: '100%', height: '100%', borderRadius: 'var(--radius)', overflow: 'hidden', position: 'relative' }}>

      {/* TOP-LEFT: Cube + gripper status */}
      <div style={{
        position: 'absolute', top: 12, left: 12, zIndex: 10,
        display: 'flex', flexDirection: 'column', gap: 5,
        pointerEvents: 'none',
      }}>
        <StatusChip
          label="CUBE"
          value={scene.cube_in_bin ? 'IN BIN ✓' : `ZONE ${scene.cube_zone}`}
          color={scene.cube_in_bin ? 'var(--accent-green)' : 'var(--accent-blue)'}
        />
        <StatusChip
          label="GRIP"
          value={scene.holding ? 'HOLDING' : 'OPEN'}
          color={scene.holding ? 'var(--accent-green)' : 'var(--text-muted)'}
          pulse={scene.holding}
        />
      </div>

      {/* LIVE ROBOT badge — shown only when connected to real backend */}
      {isLive && (
        <div style={{
          position: 'absolute', top: 12, left: '50%', transform: 'translateX(-50%)',
          zIndex: 10, pointerEvents: 'none',
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '4px 12px',
          background: 'rgba(0,214,143,0.12)',
          border: '1px solid #00d68f88',
          borderRadius: 20,
          backdropFilter: 'blur(8px)',
        }}>
          <div style={{
            width: 7, height: 7, borderRadius: '50%',
            background: '#00d68f',
            animation: 'pulse 1s ease-in-out infinite',
          }} />
          <span style={{ fontSize: 10, fontWeight: 700, color: '#00d68f', letterSpacing: '0.1em' }}>
            LIVE ROBOT
          </span>
        </div>
      )}

      {/* Joint readout — shown in live mode so you can confirm real values are streaming */}
      {isLive && (
        <div style={{
          position: 'absolute', bottom: 44, left: 12, zIndex: 10,
          pointerEvents: 'none',
          background: 'rgba(6,11,24,0.8)',
          border: '1px solid rgba(0,214,143,0.2)',
          borderRadius: 8,
          padding: '6px 10px',
          backdropFilter: 'blur(6px)',
          fontFamily: 'monospace',
        }}>
          {['shoulder_pan','shoulder_lift','elbow_flex','wrist_flex','wrist_roll','gripper'].map(k => (
            <div key={k} style={{ display: 'flex', gap: 8, fontSize: 8, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              <span style={{ color: 'var(--text-muted)', width: 88 }}>{k}</span>
              <span style={{ color: '#00d68f', fontWeight: 600 }}>
                {joints[k] !== undefined ? `${joints[k].toFixed(1)}°` : '—'}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* TOP-RIGHT: Zone legend */}
      <div style={{
        position: 'absolute', top: 12, right: 12, zIndex: 10,
        display: 'flex', flexDirection: 'column', gap: 5,
        pointerEvents: 'none',
      }}>
        {[
          { label: 'Zone A', color: '#3b82f6' },
          { label: 'Zone B', color: '#8b5cf6' },
          { label: 'BIN',    color: '#00d68f' },
        ].map(({ label, color }) => (
          <div key={label} style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '3px 8px',
            background: 'rgba(6,11,24,0.7)',
            borderRadius: 20,
            border: `1px solid ${color}44`,
            backdropFilter: 'blur(4px)',
          }}>
            <div style={{ width: 7, height: 7, borderRadius: 2, background: color, flexShrink: 0 }} />
            <span style={{ fontSize: 9, fontWeight: 600, color, letterSpacing: '0.07em' }}>{label}</span>
          </div>
        ))}
      </div>

      <Suspense fallback={<FallbackRobot />}>
        <Canvas
          camera={{ position: [0.35, 0.95, 1.9], fov: 50 }}
          shadows
          gl={{ antialias: true, alpha: false }}
          style={{ background: 'linear-gradient(180deg, #040912 0%, #0a1628 100%)' }}
          onCreated={({ gl }) => {
            gl.setClearColor('#040912');
          }}
        >
          <Lighting />
          <Stars radius={90} depth={40} count={1400} factor={2.2} fade speed={0.4} />
          <SceneObjects scene={scene} />
          <RobotArm targetJoints={joints} scene={scene} />
          <OrbitControls
            enablePan={false}
            minDistance={1.0}
            maxDistance={3.2}
            minPolarAngle={0.15}
            maxPolarAngle={Math.PI / 2 - 0.05}
            target={[0, 0.72, 0]}
          />
        </Canvas>
      </Suspense>
    </div>
  );
}
