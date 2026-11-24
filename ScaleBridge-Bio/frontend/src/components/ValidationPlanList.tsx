import React from 'react';
import { ValidationTask } from '../api/types';

interface ValidationPlanListProps {
  tasks: ValidationTask[];
}

export const ValidationPlanList: React.FC<ValidationPlanListProps> = ({ tasks }) => {
  return (
    <div className="space-y-3">
      {tasks.map((task) => (
        <div key={task.id} className="p-4 bg-white border border-slate-200 rounded-lg shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">
              Phase: {task.phase.replace('_', ' ')}
            </span>
            <span className="text-xs text-slate-500">
              {task.is_completed ? '✅ Completed' : '⏳ Pending'}
            </span>
          </div>
          <h4 className="mt-2 font-semibold text-slate-800 text-sm">{task.task_name}</h4>
          <p className="mt-1 text-xs text-slate-600">{task.description}</p>
          <div className="mt-2 text-xs bg-slate-50 p-2 rounded border border-slate-100 text-slate-700">
            🎯 <strong>Acceptance Criteria:</strong> {task.success_criteria}
          </div>
        </div>
      ))}
    </div>
  );
};
