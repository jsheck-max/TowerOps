import { clsx } from 'clsx';
import { STATUS_LABELS, type ProjectStatus } from '../types';

// --- Status Badge ---
const statusColors: Record<ProjectStatus, string> = {
  pre_construction: 'bg-yellow-100 text-yellow-800',
  active: 'bg-gray-100 text-gray-600',
  in_progress: 'bg-emerald-100 text-emerald-700',
  punch_list: 'bg-orange-100 text-orange-800',
  closeout: 'bg-indigo-100 text-indigo-800',
  complete: 'bg-gray-100 text-gray-600',
  on_hold: 'bg-red-100 text-red-800',
};

export function StatusBadge({ status }: { status: ProjectStatus }) {
  return (
    <span className={clsx('px-2.5 py-1 rounded-full text-xs font-semibold', statusColors[status] || 'bg-gray-100 text-gray-600')}>
      {STATUS_LABELS[status] || status}
    </span>
  );
}

// --- Cost Display ---
function formatDollars(n: number): string {
  if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `$${(n / 1000).toFixed(1)}K`;
  if (n > 0) return `$${n.toFixed(0)}`;
  return '$0';
}

// --- Budget / Spend Bar ---
interface BudgetBarProps {
  budget: number;
  actual: number;
  showLabel?: boolean;
}

export function BudgetBar({ budget, actual, showLabel = true }: BudgetBarProps) {
  const hasBudget = budget > 0;
  const pct = hasBudget ? Math.min((actual / budget) * 100, 150) : 0;
  const isOver = actual > budget && hasBudget;
  const isWarning = pct >= 80 && pct < 100;
  const barColor = isOver ? 'bg-red-500' : isWarning ? 'bg-amber-500' : 'bg-emerald-500';

  // If no budget set, just show the spend amount
  if (!hasBudget && actual > 0) {
    return (
      <div className="text-right">
        <span className="text-sm font-semibold text-gray-900">{formatDollars(actual)}</span>
        <span className="text-xs text-gray-400 ml-1">spent</span>
      </div>
    );
  }

  if (!hasBudget && actual === 0) {
    return <span className="text-xs text-gray-400">—</span>;
  }

  return (
    <div className="w-full">
      {showLabel && (
        <div className="flex justify-between text-xs mb-1">
          <span className={clsx('font-medium', isOver ? 'text-red-600' : 'text-gray-700')}>
            {formatDollars(actual)}
          </span>
          <span className="text-gray-400">
            of {formatDollars(budget)} ({pct.toFixed(0)}%)
          </span>
        </div>
      )}
      <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
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
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'emerald';
}

const valueColors: Record<string, string> = {
  blue: 'text-blue-600',
  green: 'text-green-600',
  red: 'text-red-600',
  yellow: 'text-amber-600',
  emerald: 'text-emerald-600',
};

export function StatCard({ label, value, sublabel, color = 'blue' }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-sm transition-shadow">
      <p className="text-sm text-gray-500 font-medium">{label}</p>
      <p className={clsx('text-2xl font-bold mt-1', valueColors[color] || 'text-gray-900')}>
        {value}
      </p>
      {sublabel && <p className="text-xs text-gray-400 mt-1">{sublabel}</p>}
    </div>
  );
}
