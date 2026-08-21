---
id: e-boostmeas
kind: experiment
title: CPU boost is a runtime sysfs toggle (measured on/off, no reboot)
supersedes: []
status: go
---
On a 2-socket server: wrote 0 then 1 to /sys/devices/system/cpu/cpufreq/boost.
Top core 3744 MHz (boost on) -> 3100 MHz (off) -> 3744 MHz (restored).
uptime unchanged across all three reads -> no reboot occurred.
