#!/usr/bin/env python3

import subprocess
from contextlib import contextmanager
from pathlib import Path

BACKUPS_USER = 'snoobackup'
BACKUP_HOME = Path('/home').resolve() / BACKUPS_USER
BACKUP_DEST = BACKUP_HOME / 'backupdata'
FILELIST_PATH = BACKUP_HOME / 'filelist'
LOCKFILE = BACKUP_HOME / '.backup-in-progress'
ACL_BACKUP_FILE = BACKUP_DEST / 'acls.bak'

RSYNC_OPTIONS = [
    '-aRPEXA', '--delete', '--exclude={}'.format(BACKUP_DEST)
]


@contextmanager
def backup_lock():
    f = LOCKFILE
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
        if file and not file.startswith('#') and Path(file).exists()
    ]

    if not files:
        return

    with backup_lock():
        subprocess.check_call(
            ['rsync'] + RSYNC_OPTIONS + files + [str(BACKUP_DEST)],
            stdout=subprocess.DEVNULL
        )
        with ACL_BACKUP_FILE.open('w') as f:
            subprocess.check_call([
                'getfacl', '-R', '.'
            ], stdout=f, cwd=str(BACKUP_DEST))

        subprocess.check_call(
            ['setfacl', '-R', '-m', 'u:{}:r'.format(BACKUPS_USER), '.'],
            cwd=str(BACKUP_DEST)
        )
        subprocess.check_call([
            'find', '.', '-type', 'd', '-exec',
            'setfacl', '-m', 'u:{}:rx'.format(BACKUPS_USER),
            '{}', '\\;'
        ], cwd=str(BACKUP_DEST))


if __name__ == '__main__':
    main()
