from concurrent.futures import ThreadPoolExecutor

def worker(args):
    name, task_id, priority = args
    print(f"Worker {name} is executing task {task_id} with priority {priority}")
    return f"Task {task_id} completed by {name}"


def do_thread(func, args, max_workers = 1):
    with ThreadPoolExecutor(max_workers=2) as executor:
        # 提交任务，传递多个参数
        future1 = executor.submit(func, args)
    
        # 获取结果
        print(future1.result())


if __name__ == "__main__":
    args = ("alice", 1, "high")
    do_thread(worker, args)
