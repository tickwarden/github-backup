"""Print safe counters to Actions stdout, never raw backup output."""
import os
import signal
import subprocess
import time
from pathlib import Path

account = os.environ['ACCOUNT']
if account not in ('tickwarden', 'IronCrest-sudo'):
    raise SystemExit('Invalid account')
root = Path(os.environ['RUNNER_TEMP'])
work = root / f'backup-{account}'
out = root / f'out-{account}'
log = root / f'raw-{account}.log'
os.umask(0o077)
work.mkdir(exist_ok=True)
out.mkdir(exist_ok=True)
command = ['timeout', '--signal=TERM', '--kill-after=30s', '4h', 'bash',
           'scripts/backup-org.sh', '--org', account, '--kind', 'user',
           '--backup-dir', str(work), '--out-dir', str(out),
           '--encrypt', 'gpg', '--keep', '999999', '--no-source', '--strict']
started = time.monotonic()
previous = None
last_change = started
child = None

def stop(signum, frame):
    raise KeyboardInterrupt

signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)

def report(final=False):
    global previous, last_change
    count = size = 0
    for directory in (work, out):
        for base, dirs, files in os.walk(directory, followlinks=False):
            for name in files:
                try:
                    file = Path(base) / name
                    if file.is_symlink():
                        continue
                    stat = file.stat()
                    count += 1
                    size += stat.st_size
                except OSError:
                    pass
    try:
        stat = log.stat()
        age = max(0, int(time.time() - stat.st_mtime))
        log_state = (stat.st_size, stat.st_mtime_ns)
    except OSError:
        age = -1
        log_state = (0, 0)
    state = (count, size, log_state)
    now = time.monotonic()
    if state != previous:
        last_change = now
        previous = state
    idle = int(now - last_change)
    print(f'[{account}] elapsed={int(now-started)}s | files={count} | size={size/1048576:.2f} MiB | log_age={age}s | unchanged={idle}s' + (' | FINAL' if final else ''), flush=True)
    if idle >= 600 and not final:
        print('::warning::No observed log/file/size change for at least 10 minutes. This is not definitive proof of a hang.', flush=True)

try:
    with log.open('wb') as output:
        child = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT,
                                 stdin=subprocess.DEVNULL, start_new_session=True)
        print(f'[{account}] Backup started. Raw output withheld; progress every 30 seconds.', flush=True)
        while True:
            report()
            try:
                rc = child.wait(timeout=30)
                break
            except subprocess.TimeoutExpired:
                pass
        report(final=True)
        print(f'[{account}] Exit code: {rc}', flush=True)
        if rc:
            print('::error::Backup failed or timed out; artifact publication blocked. Raw log not printed.', flush=True)
        raise SystemExit(rc if rc >= 0 else 1)
except KeyboardInterrupt:
    print(f'[{account}] Cancellation received.', flush=True)
    raise SystemExit(130)
finally:
    if child is not None:
        # Includes descendants even if the timeout process already exited.
        try:
            os.killpg(child.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
