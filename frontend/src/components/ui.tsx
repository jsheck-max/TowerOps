import { clsx } from 'clsx';
import { STATUS_LABELS, type ProjectStatus } from '../types';

// --- Status Badge ---
const statusColors: Record<ProjectStatus, string> = {
  pre_construction: 'bg-yellow-100 text-yellow-800',
  active: 'bg-green-100 text-green-800',
  punch_list: 'bg-orange-100 text-orange-800',
  closeout: 'bg-blue-100 text-blue-800',
  complete: 'bg-gray-100 text-gray-600',
  on_hold: 'bg-red-100 text-red-800',
};

export function StatusBadge({ status }: { status: ProjectStatus }) {
  return (
    <span className={clsx('px-2.5 py-0.5 rounded-full text-xs font-medium', statusColors[status])}>
      {STATUS_LABELS[status] || status}
    </span>
  );
}

// --- Budget Progress Bar ---
interface BudgetBarProps {
  budget: number;
  actual: number;
  showLabel?: boolean;
}

export function BudgetBar({ budget, actual, showLabel = true }: BudgetBarProps) {
  const pct = budget > 0 ? Math.min((actual / budget) * 100, 150) : 0;
  const isOver = actual > budget && budget > 0;
  const isWarning = pct >= 80 && pct < 100;

  const barColor = isOver ? 'bg-red-500' : isWarning ? 'bg-yellow-500' : 'bg-green-500';

  return (
    <div className="w-full">
      {showLabel && (
        <div className="flex justify-between text-xs mb-1">
          <span className="text-gray-500">
            ${actual.toLocaleString()} / ${budget.toLocaleString()}
          </span>
          <span className={clsx('font-medium', isOver ? 'text-red-600' : 'text-gray-600')}>
            {pct.toFixed(0)}%
          </span>
        </div>
      )}
      <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={clsx('h-full rounded-full transition-all duration-500', barColor)}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
    </div>
  );
}

// --- Stat Card ---
interface StatCardProps {
  label: string;
  value: string | number;
  sublabel?: string;
  color?: 'blue' | 'green' | 'red' | 'yellow';
}

const cardColors = {
  blue: 'bg-blue-50 text-blue-700',
  green: 'bg-green-50 text-green-700',
  red: 'bg-red-50 text-red-700',
  yellow: 'bg-yellow-50 text-yellow-700',
};

export function StatCard({ label, value, sublabel, color = 'blue' }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="text-sm text-gray-500 font-medium">{label}</p>
      <p className={clsx('text-2xl font-bold mt-1', cardColors[color]?.split(' ')[1] || 'text-gray-900')}>
        {value}
      </p>
      {sublabel && <p className="text-xs text-gray-400 mt-1">{sublabel}</p>}
    </div>
  );
}
