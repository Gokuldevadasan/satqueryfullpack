"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { useRef } from "react";
import * as THREE from "three";

function Earth() {
  const group = useRef<THREE.Group>(null);
  useFrame((state, delta) => { if (group.current) { group.current.rotation.y += delta * .055; group.current.rotation.x = THREE.MathUtils.lerp(group.current.rotation.x, state.pointer.y * .1, .03); group.current.rotation.z = THREE.MathUtils.lerp(group.current.rotation.z, state.pointer.x * .06, .03); } });
  return <group ref={group} rotation={[.15, -.45, 0]}>
    <mesh><sphereGeometry args={[2.05, 64, 64]} /><meshStandardMaterial color="#06111f" roughness={.78} metalness={.15} /></mesh>
    <mesh scale={1.018}><sphereGeometry args={[2.05, 64, 64]} /><meshBasicMaterial color="#0A84FF" transparent opacity={.055} side={THREE.BackSide} /></mesh>
    <mesh scale={1.065}><sphereGeometry args={[2.05, 48, 48]} /><meshBasicMaterial color="#1977cf" transparent opacity={.07} side={THREE.BackSide} /></mesh>
    <points><sphereGeometry args={[2.075, 36, 36]} /><pointsMaterial color="#71b9ff" size={.012} transparent opacity={.28} /></points>
  </group>;
}

export function EarthScene() { return <Canvas camera={{ position: [0, 0, 6.3], fov: 42 }} dpr={[1, 1.5]} gl={{ antialias: true, alpha: true }}><ambientLight intensity={.25} /><pointLight position={[4, 2, 4]} intensity={16} color="#0A84FF" /><pointLight position={[-4, -2, 2]} intensity={3} color="#2f88e6" /><Earth /></Canvas>; }
