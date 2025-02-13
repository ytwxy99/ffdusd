from concurrent.futures import ThreadPoolExecutor

def do_thread(func, args, workers = 1):
    with ThreadPoolExecutor(max_workers=workers) as executor:
        executor.submit(func, args)
