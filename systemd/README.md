# Scheduling with systemd

The sync script runs nightly via a systemd user timer. This approach requires no `cron`
installation and survives reboots gracefully — if the system was off at the scheduled
time, systemd will fire the job on next boot (`Persistent=true`).

## Prerequisites

- Python 3.8+ installed on the Linux server
- `polaris_to_sublime_sync.py` and `.env` deployed (see [../sync/](../sync/))
- A user account that will own the timer (does **not** need root)

## 1. Update paths in the service file

Edit `polaris-sublime-sync.service` to match where you deployed the script:

```ini
ExecStart=/usr/bin/python3 /opt/sublime-sync/polaris_to_sublime_sync.py
WorkingDirectory=/opt/sublime-sync
```

Replace `/opt/sublime-sync` with your actual deploy path.

## 2. Install the unit files

Copy both files into your systemd user directory and reload:

```bash
mkdir -p ~/.config/systemd/user
cp polaris-sublime-sync.service ~/.config/systemd/user/
cp polaris-sublime-sync.timer   ~/.config/systemd/user/
systemctl --user daemon-reload
```

## 3. Adjust the schedule

The timer is set to `23:30:00` (11:30 PM) by default. Adjust `OnCalendar` in
`polaris-sublime-sync.timer` so it fires **after** all three SSRS subscriptions
have run and delivered their CSVs to the sync mailbox. A 30-minute buffer after
your latest SSRS subscription is recommended.

## 4. Enable and start

```bash
systemctl --user enable --now polaris-sublime-sync.timer
```

## Useful commands

```bash
# Check timer status and next fire time
systemctl --user list-timers polaris-sublime-sync.timer

# View recent run logs
journalctl --user -u polaris-sublime-sync.service

# Run manually (useful for testing)
systemctl --user start polaris-sublime-sync.service

# Tail the log file directly
tail -f /path/to/polaris_sync.log
```
