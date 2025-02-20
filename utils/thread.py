import threading

def do_thread(func, args):
    thread = threading.Thread(target=func, args=args)
    thread.start()
