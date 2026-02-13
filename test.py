import os, shutil, time, argparse, stat

# Run as Administrator. This script safely clears files from C:\Windows\Temp.
# Default: removes files older than 7 days. Use --all to remove everything (use with caution).

def norm_path(p):
    return os.path.normcase(os.path.abspath(os.path.realpath(p)))

def confirm_base(path, base):
    p = norm_path(path)
    b = norm_path(base)
    return p == b or p.startswith(b + os.sep)

def remove_file(path):
    try:
        os.chmod(path, stat.S_IWRITE)
        os.remove(path)
        return True, None
    except Exception as e:
        return False, e

def remove_dir(path):
    try:
        shutil.rmtree(path)
        return True, None
    except Exception as e:
        return False, e

def clear_temp(base_path, days=7, remove_all=False, dry_run=True):
    now = time.time()
    age_limit = days * 86400
    files_deleted = 0
    dirs_deleted = 0
    errors = []
    for root, dirs, files in os.walk(base_path, topdown=False):
        for name in files:
            fp = os.path.join(root, name)
            try:
                mtime = os.path.getmtime(fp)
            except Exception as e:
                errors.append((fp, e))
                continue
            age = now - mtime
            should = remove_all or (age > age_limit)
            if should:
                if dry_run:
                    print("Would remove file:", fp)
                    files_deleted += 1
                else:
                    ok, err = remove_file(fp)
                    if ok:
                        files_deleted += 1
                    else:
                        errors.append((fp, err))
        for name in dirs:
            dp = os.path.join(root, name)
            # if directory is empty -> remove; if remove_all -> remove anyway
            try:
                is_empty = not any(os.scandir(dp))
            except Exception as e:
                errors.append((dp, e))
                continue
            if remove_all or is_empty:
                if dry_run:
                    print("Would remove dir: ", dp)
                    dirs_deleted += 1
                else:
                    ok, err = remove_dir(dp)
                    if ok:
                        dirs_deleted += 1
                    else:
                        errors.append((dp, err))
    return files_deleted, dirs_deleted, errors

def main():
    parser = argparse.ArgumentParser(description="Clear C:\\Windows\\Temp safely.")
    parser.add_argument("--path", default=r"C:\Windows\Temp", help="Target temp folder (must be under C:\\Windows\\Temp)")
    parser.add_argument("--days", type=int, default=7, help="Remove files older than this many days.")
    parser.add_argument("--all", action="store_true", help="Remove all files/directories (use with caution).")
    parser.add_argument("--doit", action="store_true", help="Perform deletions. Omitting keeps dry-run mode.")
    args = parser.parse_args()

    base = r"C:\Windows\Temp"
    if not confirm_base(args.path, base):
        print("Refusing to operate outside", base)
        return

    print("Target:", args.path)
    print("Mode:", "ALL" if args.all else f"older than {args.days} days")
    print("Action:", "execute deletions" if args.doit else "dry-run (no changes)")

    files_deleted, dirs_deleted, errors = clear_temp(args.path, days=args.days, remove_all=args.all, dry_run=not args.doit)

    print(f"Files targeted: {files_deleted}, Dirs targeted: {dirs_deleted}")
    if errors:
        print("Some items could not be removed (permission/in-use):")
        for p, e in errors[:20]:
            print(" ", p, "->", e)

if __name__ == "__main__":
    main()