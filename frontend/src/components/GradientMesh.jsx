function GradientMesh() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden"
    >
      <div className="absolute -left-24 -top-32 h-80 w-80 rounded-full bg-[#B7D8C7]/25 blur-3xl" />
      <div className="absolute right-[-8rem] top-1/4 h-96 w-96 rounded-full bg-[#DCE5B8]/20 blur-3xl" />
      <div className="absolute bottom-[-10rem] left-1/3 h-96 w-96 rounded-full bg-[#D5C58A]/15 blur-3xl" />
    </div>
  )
}

export default GradientMesh
