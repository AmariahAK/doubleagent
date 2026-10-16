# Deployment through an EDR

Running the collectors through an EDR remote shell, for a collection or a
fleet inventory.

## Collection

An EDR (endpoint detection and response) product's remote shell is the
usual way to reach a host: CrowdStrike Falcon RTR (Real Time Response),
SentinelOne RemoteOps (Remote Operations, which runs a script on a host as
a console task), Microsoft Defender for Endpoint Live Response, or Palo
Alto Networks Cortex XDR (extended detection and response) Live Terminal.

The script is a single file with no interactive prompts, reads nothing from
stdin, and writes everything under `-o` (`-OutputDir` in PowerShell).
Upload the script, run it with `-o` pointing at a directory you can
retrieve from, then pull the archive (`.tar.gz`; `.tar` or `.zip` after an
archiver fallback, see [output.md](output.md#archiver-fallbacks)). Use `-q`
(`-Quiet`) to keep the console output to the final summary.

On Windows, files held open by a running editor still copy, and paths
longer than 260 characters are collected without any host setting, under
Windows PowerShell 5.1 as well; see
[windows.md](windows.md#locked-files-and-long-paths).

### Console output arrives at the end

The collector writes its progress as it goes: one line per user, catalog
match and project, to stderr unless `-q` is given and always to the log
file under `-o`, one line at a time (the sh collector appends each line
with its own `printf`, the PowerShell collector's log writer flushes after
every line). In a local terminal that progress is live.

The EDR consoles are what hold it back. Running the collector through RTR
`runscript`, no output appeared until the script had finished (observed in
October 2026, recorded in
[issue 100](https://github.com/seanthegeek/doubleagent/issues/100)), and
the consoles run a script as one command whose result comes back when it
ends. A long collection therefore shows nothing until the summary; that is
the console's behaviour, not a hang. `-q` changes nothing here: it removes
the progress lines from stderr, but the console holds stdout and stderr
alike until the end.

The consoles also bound how long one command may run:

| Console | Command limit | Source |
| --- | --- | --- |
| CrowdStrike RTR `runscript` | Set with `-Timeout=<seconds>`. The run-script command of the Falcon integration for Cortex XSOAR (Palo Alto Networks' security orchestration, automation and response platform) documents a maximum of 600 seconds (default 30). The RTR session itself times out after 10 minutes unless you interact with it. | [Cortex XSOAR's CrowdStrike Falcon integration reference](https://xsoar.pan.dev/docs/reference/integrations/crowdstrike-falcon) (the 600-second maximum); a CrowdStrike maintainer in [CrowdStrike/psfalcon discussion 249](https://github.com/CrowdStrike/psfalcon/discussions/249), who sets a 600-second command timeout and recommends launching a long script as a separate process and collecting its results afterwards; the [UAC documentation on Falcon RTR](https://tclahr.github.io/uac-docs/using_uac_with_cs_falcon_rtr/) (the session timeout, and a background run of UAC, the Unix-like Artifacts Collector, watched through its log) |
| Defender Live Response `RunScript` | Times out after 10 minutes. | [Run live response commands on a device](https://learn.microsoft.com/en-us/defender-endpoint/api/run-live-response) |
| SentinelOne RemoteOps script task | Set per task in the console; the script's output is read from the task's status in the console once the task has run. | A [Safety deployment guide for SentinelOne](https://docs.safetycli.com/safety-docs/deployment/deployment/sentinelone), which recommends a timeout of at least 1800 seconds for its own long-running script |

(Sources fetched 2026-10-15.)

### Long or watched collections

When a collection may run longer than the console's command limit, or you
want to watch it, start the collector detached from the console's command
so the command returns at once, then read the log from the same session.
This is a manual pattern; a built-in option for it is tracked in
[issue 101](https://github.com/seanthegeek/doubleagent/issues/101).

On macOS, Linux and the BSDs, through RTR `runscript -Raw` or the
console's equivalent (the paths are examples):

```sh
nohup sh /tmp/ir/collect-agent-artifacts.sh -o /tmp/ir -q >/dev/null 2>&1 &
```

On Windows, give the script's full path; a path with spaces needs its own
quotes inside the argument string:

```powershell
Start-Process powershell.exe -WindowStyle Hidden -ArgumentList '-ExecutionPolicy Bypass -File C:\ir\Collect-AgentArtifacts.ps1 -OutputDir C:\ir -Quiet'
```

The log is created in the output directory when the run starts, under
the name [output.md](output.md#output-files) gives,
`<host>_<UTC time>_agent-artifacts.log` (for example
`host_20261003T165531Z_agent-artifacts.log`). The lines written during
the walk start with a UTC timestamp. Read it with `cat` or `tail` (RTR's
`cat` on Windows, or `Get-Content -Tail` in PowerShell) as often as you
like:

- One line per user with agent state, per catalog match (the agent
  name in brackets, then the matched path) and per project is written
  as the walk reaches it, so the lines show which home and agent the
  collector is on. The log does not keep a running count of files; the
  counts are in the summary at the end.
- `Archiving` marks the end of the walk; the archive is being written and
  is not complete yet.
- The `done:` line, `<UTC time> done: <archive path> (<size> bytes, sha256
  <hex>)`, is written once the archive is complete and hashed, as
  [output.md](output.md#stdout-summary) describes. Pull the archive only
  after it appears. It is the last line, except that the PowerShell
  collector adds one more line when it cannot remove its staging
  directory.

Then `get` the archive and its `.sha256` file. With the output sent to
`/dev/null` the stdout summary is not kept, but the same counts are in
`collection.json` beside the archive; see
[output.md](output.md#collectionjson). A run that stops before it creates
the log (a usage error, an output directory that cannot be created)
leaves no log at all, and its message went to the discarded stderr; run
the same command in the foreground to see it.

### Runtime

A run on a developer workstation with several agents installed takes well
under a minute. On a heavy user's host it takes longer: the time grows
with the number and size of the files collected, since each one is copied
and hashed, and long agent histories (years of transcripts, large
per-project histories, Docker volumes) can make it minutes rather than
seconds. Plan for the console limits above, and use the detached pattern
when in doubt.

## Fleet inventory

For a fleet inventory, run the script with `--inventory` (`-Inventory`) and
no `-o`: nothing is uploaded back or left on the host, and the console
output of the run is the result. Save each host's stdout as its own file
(the EDR console's output export or a copy and paste of the response) and
pass the files to the analyzer's `inventory` command. Add `-q` so stderr
stays empty; stderr never mixes into stdout, but some consoles show both
together. The lines are described in [inventory.md](inventory.md).

## Access times

Copying a file updates its `atime` on filesystems that track it. The
manifest records the pre-copy `atime` from `lstat`, taken before the copy.
On a disk image, mount it read-only with `noatime`.
