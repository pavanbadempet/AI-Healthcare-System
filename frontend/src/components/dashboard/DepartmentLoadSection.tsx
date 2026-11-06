import { motion } from "framer-motion";

interface DepartmentLoad {
  dept: string;
  load: number;
  status?: string;
}

interface DepartmentLoadSectionProps {
  departmentLoads?: DepartmentLoad[];
}

export function DepartmentLoadSection({ departmentLoads }: DepartmentLoadSectionProps) {
  const loads = departmentLoads?.length
    ? departmentLoads
    : [
        { dept: "Cardiology", load: 88, status: "Critical" },
        { dept: "Pulmonology", load: 64, status: "Stable" },
        { dept: "Nephrology", load: 42, status: "Optimal" },
        { dept: "Endocrinology", load: 76, status: "Elevated" },
      ];

  return (
    <div className="panel overflow-hidden">
      <div className="panel-header bg-[rgba(15,15,17,0.5)]">
        <h2 className="section-title">Department Load Allocations</h2>
      </div>
      <div
        className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
        role="region"
        aria-label="Department load indicators"
      >
        {loads.map((dept) => (
          <div key={dept.dept} className="space-y-2">
            <div className="flex justify-between text-[11px] font-mono uppercase tracking-wider">
              <span className="text-[var(--text-secondary)]">{dept.dept}</span>
              <span
                className={
                  dept.load > 80
                    ? "text-[var(--danger)] font-bold"
                    : dept.load > 70
                      ? "text-[var(--warning)] font-bold"
                      : "text-[var(--success)] font-bold"
                }
              >
                {dept.load}%
              </span>
            </div>
            <div className="h-1.5 w-full bg-[var(--border)] rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${dept.load}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className={`h-full ${
                  dept.load > 80
                    ? "bg-[var(--danger)]"
                    : dept.load > 70
                      ? "bg-[var(--warning)]"
                      : "bg-[var(--success)]"
                }`}
                role="progressbar"
                aria-valuenow={dept.load}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`${dept.dept} load: ${dept.load}%`}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
