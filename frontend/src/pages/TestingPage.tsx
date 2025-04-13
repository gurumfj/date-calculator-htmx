import PageNavbar from "../components/layout/components/PageNavbar";
import { useQuery } from "@tanstack/react-query";

interface DueDate {
  string: string;
  isRecurring: boolean;
  date: string;
  datetime?: string | null | undefined;
  timezone?: string | null | undefined;
  lang?: string | null | undefined;
}

interface Duration {
  amount: number;
  unit: string;
}

interface Task {
  assignee_id: string | null;
  assigner_id: string | null;
  comment_count: number;
  is_completed: boolean;
  content: string;
  created_at: string;
  creator_id: string;
  description: string;
  due: DueDate | null;
  id: string;
  labels: string[] | null;
  order: number;
  parent_id: string | null;
  priority: number;
  project_id: string;
  section_id: string | null;
  url: string;
  duration: Duration | null;
  sync_id: string | null;
}

const TestingPage: React.FC = () => {
  const {
    data: tasks = [],
    error,
    isLoading,
  } = useQuery<Task[]>({
    queryKey: ["tasks"],
    queryFn: async () => {
      const base_api = "http://localhost:8888/api/todoist";
      const get_tasks_path = "/tasks";
      const response = await fetch(`${base_api}${get_tasks_path}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      console.log(result);
      return result;
    },
  });

  if (isLoading) return <div>載入中...</div>;
  if (error) return <div>錯誤: {error.message}</div>;

  return (
    <>
      <PageNavbar title="測試" />
      <div className="p-4">
        <h2 className="text-xl font-semibold mb-4">測試</h2>
        <div className="text-gray-600">
          <p>此頁面用於測試功能。</p>
          {tasks.length > 0 ? (
            tasks.map((task) => (
              <div key={task.id} className="border-b py-2">
                <p className="font-medium">{task.content}</p>
                {task.due && <p className="text-sm">到期日: {task.due.date}</p>}
              </div>
            ))
          ) : (
            <p>沒有任務</p>
          )}
        </div>
      </div>
    </>
  );
};

export default TestingPage;
