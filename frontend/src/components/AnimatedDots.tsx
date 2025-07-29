import { useState, useEffect } from 'react';

interface AnimatedDotsProps {
  className?: string;
}

export default function AnimatedDots({ className = '' }: AnimatedDotsProps) {
  const [dotCount, setDotCount] = useState(1);

  useEffect(() => {
    const interval = setInterval(() => {
      setDotCount(prev => prev === 3 ? 1 : prev + 1);
    }, 500); // Change dots every 500ms

    return () => clearInterval(interval);
  }, []);

  return (
    <span className={className}>
      {'.'.repeat(dotCount)}
    </span>
  );
}
