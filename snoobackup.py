#!/usr/bin/env python3

from pathlib import Path
from contextlib import contextmanager
import subprocess
import shlex

BACKUP_HOME = Path('/home/snoobackup')
BACKUP_DEST = BACKUP_HOME / 'backupdata'
FILELIST_PATH = BACKUP_HOME / 'filelist'


@contextmanager
def backup_lock():
    f = BACKUP_HOME / '.backup-in-progress'
    if f.exists():
        raise FileExistsError("Lock file exists! {}".format(f))

    f.touch()
    yield
    f.unlink()


def main():
    with FILELIST_PATH.open(encoding='utf-8') as f:
        file_list = f.read().splitlines()

    files = [
        file for file in file_list
        if not file.startswith('#') and Path(file).exists()
    ]

    if not files:
        return

    with backup_lock():
        subprocess.check_call(
            ['rsync', '-aRPEXA', '--delete'] + files + [str(BACKUP_DEST)],
            stdout=subprocess.DEVNULL
        )
        with (BACKUP_DEST / 'acls.bak').open('w') as f:
            subprocess.check_call([
                'getfacl', '-R', '.'
            ], stdout=f, cwd=str(BACKUP_DEST))

        subprocess.check_call(shlex.split('setfacl -R -m u:snoobackup:r .'), cwd=str(BACKUP_DEST))
        subprocess.check_call(
            shlex.split('find . -type d -exec setfacl -m u:snoobackup:rx {} \;'),
            cwd=str(BACKUP_DEST)
        )


if __name__ == '__main__':
    main()

