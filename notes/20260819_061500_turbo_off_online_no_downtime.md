---
id: c-turbooff
kind: claim
title: turbo-off is applied online with no downtime
justified_by: [e-boostmeas]
refuted_by: []
supersedes: [c-downtime]
status: go
---
## 3. What we now conclude
A systemd unit writes boost=0 + governor=performance live; it persists across reboot.

## 4. What would defeat it
An experiment showing boost cannot be set without a reboot (would revive c-downtime). None found.
