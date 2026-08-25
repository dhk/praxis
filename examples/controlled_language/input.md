# Deployment Note

Please note that the migration was approved by the platform group in order to
retire the legacy queue before the end of Q3.

Prior to the cutover, the standby cluster is provisioned and the checksums are
verified, and then the read traffic is shifted across in two stages so that any
regression in the 99th-percentile latency shows up before the write path moves.

Operators should utilize the runbook at https://example.com/runbook, and they
must confirm that the replica lag stays under 250 ms.
