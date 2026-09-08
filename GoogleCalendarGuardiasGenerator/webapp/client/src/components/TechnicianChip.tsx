import type { CSSProperties } from "react";
import { useDraggable } from "@dnd-kit/core";

interface Props {
  nombre: string;
  color: string;
}

export function TechnicianChip({ nombre, color }: Props) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: `tecnico:${nombre}`,
    data: { tecnico: nombre, color }
  });

  const style: CSSProperties = transform
    ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`, zIndex: 50 }
    : {};

  return (
    <div
      ref={setNodeRef}
      style={{ ...style, background: color }}
      className={`technician-chip${isDragging ? " dragging" : ""}`}
      {...listeners}
      {...attributes}
    >
      {nombre}
    </div>
  );
}
