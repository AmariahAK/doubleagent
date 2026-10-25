# Lab VMs

Three virtual machines, one each for Windows, macOS and Ubuntu, are where
the project watches what an AI agent writes to a real system. Each is kept
as a clean snapshot that holds what a developer's machine has and nothing
else. A [real-install round](../AGENTS.md#real-install-rounds) reverts the
VM to that snapshot, installs the agent under test, exercises it one step
at a time while a listing of the agent's directories is taken over SSH
after each step, runs the collector inside the VM, pulls the archive to
the analyst machine, and reverts the VM again before the next agent. The
snapshot is the starting point of every round, so what it holds decides
what the agent can do and what the round can see.

The sections below say why development tools are in the snapshots, what
the host machine must provide for the VMs to do their job, how the main
session reaches each VM over SSH, how each VM is built from a clean
install, and which versions the snapshots hold.

## Why the VMs hold development tools

A round records what an agent does on a host, and an agent given a bare
VM can only show what it does without tools. The snapshot therefore holds
what a developer's machine has: the languages and their package managers,
the compilers, version control, an editor and, where the host allows, a
container engine. With them the agent can build, test, install, clone,
commit and run whatever it is asked to, and the listings the round takes
after each step, with the collector's archive, record that activity for
analysis: the packages it
installed, the repositories it cloned, the commits it made, the tools it
ran and the files each of those left behind.

The tools are installed and never launched, nothing is signed in (no
GitHub account in `gh`, no editor opened), the package managers' caches
are cleaned, and the round's first listing is taken from the snapshot
before the agent is installed. A directory a tool creates on first use
(`~/go`, `~/.cargo`, `~/.gem`, the pipx directories, uv's cache) then
appears in the diff of the step in which the agent first used that tool,
which is itself evidence of what it did.

The snapshot holds what a developer has, not what this repository's CI
runs: its linters (shellcheck, shfmt, PSScriptAnalyzer, ruff) are not
installed. An agent that wants one installs it during the round, and the
install is part of the record.

Automatic updates and scheduled reboots are turned off in each clean
snapshot: Windows Update's active hours and restart policy, macOS
automatic updates, and the automatic reboot of Ubuntu's
unattended-upgrades. An update in the middle of a round writes files the
agent did not, and a reboot ends the agent's open session. A snapshot is
also taken at each pause of a round, so an unplanned reboot costs the
steps since that snapshot, not the round.

## The host

Four things about the host decide what the VMs can do:

- **A Mac, for the macOS VM.** Apple's software licence allows macOS to
  run as a guest only on Apple hardware, so a lab that covers macOS needs
  a Mac as its host. Windows and Linux guests run on any host, so a lab
  on other hardware covers those two platforms and leaves macOS to a Mac.
- **Memory.** A running VM holds a large share of the host's memory, so
  on a host with little of it only one VM runs at a time, and the
  collector's smoke tests and the analyzer's tests are not run on the
  host beside one; see
  [Validation and testing](../AGENTS.md#validation-and-testing).
- **Nested virtualization.** A guest can run a hypervisor of its own
  only when the host passes the hardware virtualization extensions
  through. Whether it does depends on the host's hypervisor and chip:
  Parallels Desktop on Apple silicon does it for Linux guests alone, on
  an M3 or later chip with macOS 15 or later and the Pro or Business
  edition, and never for a Windows on ARM guest or a macOS guest; a
  hypervisor on an x86-64 host usually offers it to every guest as a
  setting. Without it there is no WSL 2 (the Windows Subsystem for Linux,
  which runs a Linux kernel in a Hyper-V virtual machine) in a Windows
  VM and no Virtualization framework (Apple's hypervisor API) in a macOS
  VM, and an agent feature that needs a container in such a VM is
  recorded in the round as a feature the VM cannot run. What that means
  for Docker in each VM is under [Docker](#docker).
- **Disk.** A snapshot merge, which deleting an older snapshot triggers,
  needs free space beside the virtual disk on the same volume, and the
  virtual disk only grows across revert-and-reinstall cycles. A VM on an
  external disk needs the host kept awake while it runs, because a bus
  sleep under a running VM or a merging snapshot damages the bundle.

## SSH access

During a round the main session runs `ssh` and `scp` from its tool calls:
the listing script after every step, copying `analyzer/tools/shape.py` and
the collector into the VM, pulling the archive and the probe output out,
and deleting the outputs it left behind. The person at the VM uses its
console; the agent never does.

A tool call has no terminal, so a password or passphrase prompt cannot be
answered and the command hangs or fails, and an agent cannot be relied on
to reach a running `ssh-agent` either. The lab therefore uses one
dedicated ed25519 key with no passphrase, generated for the lab alone.
What limits the exposure: the key is authorized only for the lab user in
VMs on a host-only network that are reverted after every round, so it
opens nothing a revert does not erase; `IdentitiesOnly yes` means the
agent never offers the developer's other keys to the VMs; the private key
is mode 600 under `~/.ssh` on the host, outside any repository, and never
enters a VM; and revoking it is removing the public key from the VM's
authorized file and retaking the snapshot. Generate it on the host:

```sh
ssh-keygen -t ed25519 -N '' -C doubleagent-lab -f ~/.ssh/doubleagent_lab
```

The connection flags live in an ssh config file passed with `-F` rather
than typed per call: one file keeps every call identical, and fish does
not word-split a flag string held in a variable. The file sits with the
round's other tooling outside the repository, holds one `Host` alias per
VM, and points `UserKnownHostsFile` at a known-hosts file of its own,
because a rebuilt VM gets new host keys and would leave a stale entry in
the developer's own file:

```text
# ssh -F <this file> <alias>
Host winvm
  HostName <address the hypervisor gave the Windows VM>
  User <lab user>
  IdentityFile ~/.ssh/doubleagent_lab
  IdentitiesOnly yes
  UserKnownHostsFile <lab directory>/known_hosts
  StrictHostKeyChecking accept-new

Host macvm
  HostName <address the hypervisor gave the macOS VM>
  User <lab user>
  IdentityFile ~/.ssh/doubleagent_lab
  IdentitiesOnly yes
  UserKnownHostsFile <lab directory>/known_hosts
  StrictHostKeyChecking accept-new

Host ubuvm
  HostName <address the hypervisor gave the Ubuntu VM>
  User <lab user>
  IdentityFile ~/.ssh/doubleagent_lab
  IdentitiesOnly yes
  UserKnownHostsFile <lab directory>/known_hosts
  StrictHostKeyChecking accept-new
```

The SSH server and the authorized public key are part of each clean
snapshot, so a round's first listing can be taken before the agent is
installed; the snapshot holds no lab directory, which the round creates
and deletes before the VM is released. What each OS needs is under its
heading below, the server first and the key after it.

## Windows

Windows 11. Everything comes from the community source of `winget`, the
package manager Windows ships, whose manifests download each installer
from the vendor's own release host and pin its SHA-256, and `winget` picks
the build for the guest's architecture. On an Apple silicon host the guest
is Windows 11 on ARM, and the ids below all have native ARM64 builds
except two x64 packages that install the native ARM64 pieces themselves:
the Python install manager, which fetches the ARM64 runtime, and the
Visual Studio Build Tools bootstrapper, which installs the ARM64
compilers. Run from an elevated PowerShell:

```powershell
winget install --id Python.PythonInstallManager -e --accept-package-agreements --accept-source-agreements
py install 3.15
winget install --id Git.Git -e --accept-package-agreements --accept-source-agreements
winget install --id GitHub.cli -e --accept-package-agreements --accept-source-agreements
winget install --id OpenJS.NodeJS.LTS -e --accept-package-agreements --accept-source-agreements
winget install --id Microsoft.VisualStudioCode -e --accept-package-agreements --accept-source-agreements
winget install --id Microsoft.VisualStudio.BuildTools -e --accept-package-agreements --accept-source-agreements --override "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.VC.Tools.ARM64 --includeRecommended"
winget install --id Rustlang.Rustup -e --accept-package-agreements --accept-source-agreements
winget install --id GoLang.Go -e --accept-package-agreements --accept-source-agreements
winget install --id RubyInstallerTeam.RubyWithDevKit.4.0 -e --accept-package-agreements --accept-source-agreements
winget install --id Microsoft.OpenJDK.25 -e --accept-package-agreements --accept-source-agreements
winget install --id Microsoft.PowerShell -e --accept-package-agreements --accept-source-agreements
winget install --id astral-sh.uv -e --accept-package-agreements --accept-source-agreements
py -m pip install --user pipx
py -m pipx ensurepath
```

- `Python.PythonInstallManager` is the Python install manager, the way
  python.org now installs Python on Windows: the 3.15 documentation marks
  the full `.exe` installer and the old `py` launcher deprecated. Its `py`
  command downloads a runtime from python.org's index, so `py install
  3.15` pins the line and installs the guest's ARM64 or x64 build; the
  first install offers to add `%LocalAppData%\Python\bin`, the directory
  of the `python3.15` aliases, to the user PATH, and `py` works without
  it. The python.org documentation installs the same package through
  winget's Microsoft Store source as `9NQ7512CXL7T`.
- The Build Tools go first, because rustup's default toolchain on Windows
  is the MSVC one (Microsoft's C and C++ compiler and linker) and wants
  the linker present. The `--override` string
  replaces winget's own silent switches, so it carries `--wait --passive`
  itself; the VCTools workload alone installs the x64 and x86 compilers,
  hence the explicit ARM64 component, which an x64 guest can leave out.
  This is the largest install of the set.
- `Microsoft.VisualStudio.BuildTools` is the 2026 release (version 18);
  the ids with a year, such as `Microsoft.VisualStudio.2022.BuildTools`,
  are the older lines.
- RubyInstaller is the Windows distribution that ruby-lang.org links, and
  its ARM64 package exists from 3.4.1-2 on; the DevKit's compilers are
  native and its MSYS2 half runs as x64 under emulation. winget does not
  run the post-install `ridk install` that sets MSYS2 up for native gems;
  run `ridk install 1 3` once if the snapshot should build them.
- pipx has no winget package; its own documented install is through the
  Python just installed, and `ensurepath` adds `%USERPROFILE%\.local\bin`,
  where pipx and uv both put the tools they install, to the user PATH.
- `Microsoft.PowerShell` is PowerShell 7 beside the Windows PowerShell 5.1
  the collector targets, so the VM runs both sides of the collector's test
  matrix.
`winget show --id <id>` prints the installer URL and hash a package would
install, for checking a package before trusting it.

### SSH

Windows ships an OpenSSH server as an optional capability, off by default.
In the VM, from an elevated PowerShell, install it, start it at every
boot, and make sure the inbound rule the capability normally creates is
there:

```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic
if (-not (Get-NetFirewallRule -Name OpenSSH-Server-In-TCP -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -Name OpenSSH-Server-In-TCP -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
}
```

The lab user is an administrator, so the collector can run elevated and
the SSH session holds the backup privilege that reads other users'
profiles. That changes where the key goes: for a member of Administrators,
sshd reads `C:\ProgramData\ssh\administrators_authorized_keys` and
ignores the user's own `~\.ssh\authorized_keys`, and it refuses the
file unless Administrators and SYSTEM are the only accounts that can read
it. Password authentication is on by default, which is what the first
copy uses. From the host, with the password once:

```sh
scp -F <lab directory>/sshconfig ~/.ssh/doubleagent_lab.pub winvm:C:/ProgramData/ssh/administrators_authorized_keys
```

Back in the VM, from an elevated PowerShell, set the permissions sshd
requires:

```powershell
icacls.exe C:\ProgramData\ssh\administrators_authorized_keys /inheritance:r /grant 'Administrators:F' /grant 'SYSTEM:F'
```

Then `ssh -F <lab directory>/sshconfig winvm hostname` from the host
prints the VM's name without a prompt. The login shell is cmd.exe, so
anything with a pipe or nested quotes goes in a `.ps1` file under the lab
directory and runs with `powershell -File`.

## macOS

macOS. The VM starts with no package manager, so the
Command Line Tools (Apple's package with `git`, `clang` and
`/usr/bin/python3`) come first, then Homebrew, then the toolchain as
Homebrew formulas (command-line tools Homebrew builds or unpacks) and one
cask (Homebrew's recipe for a GUI app, which downloads the vendor's own
build and moves it into `/Applications`).

`xcode-select --install` opens a dialog, so over SSH use the on-demand
marker that Homebrew's installer uses:

```sh
touch /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress
softwareupdate -l | grep 'Command Line Tools'
sudo softwareupdate -i 'Command Line Tools for Xcode-26.4'   # the label the list printed
rm /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress
```

Homebrew's installer asks for the sudo password once, so it runs in the
VM's own Terminal. It does not put Homebrew on the PATH itself: its
"Next steps" print the three lines that do, a blank line and the
`shellenv` line for the login file, then the same `shellenv` line for
the current shell, and they come before the first `brew` call. When
`~/.zprofile` already holds the line, after a second run of the
installer or when the line was added first, the installer prints only
the last of the three, since the next login shell is covered:

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
echo >> ~/.zprofile
echo 'eval "$(/opt/homebrew/bin/brew shellenv zsh)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv zsh)"
brew analytics off
```

Then:

```sh
brew install python@3.15 git gh node@24 go rustup ruby openjdk@25 pipx uv powershell
brew install --cask visual-studio-code
brew link --overwrite node@24
echo 'export PATH="$(brew --prefix)/lib/ruby/gems/4.0.0/bin:$(brew --prefix)/opt/node@24/bin:$(brew --prefix)/opt/rustup/bin:$PATH"' >> ~/.zprofile
. ~/.zprofile
rustup default stable
sudo ln -sfn "$(brew --prefix)/opt/openjdk@25/libexec/openjdk.jdk" /Library/Java/JavaVirtualMachines/openjdk-25.jdk
brew cleanup -s
```

- `node@24`, `openjdk@25` and `rustup` are keg-only: Homebrew installs
  them under its `opt/` directory without linking them into its `bin`,
  because macOS ships its own Java, the versioned Node would shadow the
  `node` formula, and `rustup` conflicts with the `rust` formula. `ruby`
  is linked, and Homebrew's `bin` comes before Apple's Ruby 2.6 in
  `/usr/bin` on the PATH, but the commands that `gem install` adds go
  into `lib/ruby/gems/4.0.0/bin` under the prefix, which nothing links.
  Each formula says so in the caveats it prints after installing, and
  the `link`, PATH and `ln` lines are those caveats' instructions: they
  make the kegs and the gem directory the ones a shell finds, the PATH
  line is read back into the current shell before `rustup default
  stable` needs it, and the `ln` line is Homebrew's documented way to
  register a JDK with `java_home`. Without the PATH line, `cargo` and
  `rustc`, which live in rustup's keg, are not found.
- `node@24` rather than `node`: Homebrew's `node` formula tracks the
  current release, and `node@24` is the long-term support line, the one
  `OpenJS.NodeJS.LTS` installs on Windows. `openjdk@25` rather than
  `openjdk` for the same reason, since `openjdk` is the current non-LTS
  Java.
- `python@3.15` is the Python the `pipx` formula depends on, so Homebrew
  installs it with `pipx` whether or not the line names it. Naming an
  older Python instead (`python@3.13`) installs two: both land under
  `opt/`, and `python3` in Homebrew's `bin` is the newer one, since only
  the current formula links the unversioned names.
- `powershell` is a formula, not a cask: the `powershell` cask was
  disabled on 2026-09-01 because its package fails Homebrew's Gatekeeper
  check, and the formula has arm64 bottles for macOS 26.
- The collector's smoke test runs there under a bash 3.2 `/bin/sh`, the
  shell CI does not test, and validates its JSON once `python3` exists.
- VS Code's cask installs the same universal build the vendor's download
  button serves and links the `code` command into Homebrew's `bin`, so
  the app is never opened before the snapshot. The app writes
  `~/Library/Application Support/Code` and `~/.vscode` on first launch.
- `brew cleanup -s` drops the downloaded bottles from
  `~/Library/Caches/Homebrew`. Homebrew still leaves that directory,
  `~/Library/Logs/Homebrew` and the pipx and rustup directories under the
  home, so the round's first listing is taken from the snapshot, not from
  a fresh install.

Not every hypervisor snapshots a macOS guest. When the VM has no
snapshot control, the finished VM is cloned as the clean copy and
reverted by cloning it again.

### SSH

macOS ships the server and calls it Remote Login. Turn it on in System
Settings under General, then Sharing, or from the VM's Terminal:

```sh
sudo systemsetup -setremotelogin on
```

From the host, with the password once; `ssh-copy-id` creates `~/.ssh`
and `authorized_keys` in the VM with the modes sshd requires:

```sh
ssh-copy-id -i ~/.ssh/doubleagent_lab.pub -o IdentitiesOnly=yes <lab user>@<address>
```

Then `ssh -F <lab directory>/sshconfig macvm hostname` from the host
prints the VM's name without a prompt.

## Ubuntu

Ubuntu, where `sh` is dash and bash and busybox are a package away, so
the collector's smoke test runs under all three there in a few minutes
each. Most of the toolchain is in Ubuntu's own archive; the rest comes from the
vendor's documented route:

```sh
sudo apt install git python3 python3-pip pipx ruby-full golang-go openjdk-25-jdk
curl -LsSf https://astral.sh/uv/install.sh | sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
```

- `gh` comes from GitHub's own apt repository, Node from NodeSource's
  repository for the LTS line, and VS Code from Microsoft's `.deb`, each
  as the vendor's install page documents for Ubuntu.
- PowerShell: Microsoft's apt repository ships amd64 packages only, so an
  arm64 VM takes the `.deb` published on the PowerShell GitHub release
  (`powershell_<version>-1.deb_arm64.deb`) and installs it with
  `sudo apt install ./<file>`; an amd64 VM uses the repository as the
  PowerShell install page documents. The `.deb` registers no apt source,
  so it does not update itself. The snap (`sudo snap install powershell
  --classic`) is the alternative on both and runs a release or two
  behind.
- Docker Engine comes from Docker's own apt repository, under
  [Docker](#docker).

### SSH

Ubuntu Desktop installs no SSH server (Ubuntu Server offers one during
installation). In the VM:

```sh
sudo apt install openssh-server
sudo systemctl enable --now ssh
```

From the host, with the password once:

```sh
ssh-copy-id -i ~/.ssh/doubleagent_lab.pub -o IdentitiesOnly=yes <lab user>@<address>
```

Then `ssh -F <lab directory>/sshconfig ubuvm hostname` from the host
prints the VM's name without a prompt.

## Docker

Docker Desktop runs containers inside a Linux virtual machine of its own,
so inside a guest it needs nested virtualization; Docker Engine on Linux
runs containers on the guest's own kernel and needs none. So the Ubuntu
VM runs containers on any host, and is where the
[agent lab](../lab/README.md) and the container-deployed agents are
exercised; the Windows and macOS lines below belong in those VMs'
snapshots only on a host that gives them nested virtualization, and are
recorded with their requirements for a host that does. The versions are
the current releases on 2026-10-23.

### Docker Engine on Ubuntu

Docker's apt repository carries Docker Engine for Ubuntu 26.10, 26.04 LTS,
24.04 LTS and 22.04 LTS, on amd64, arm64, armhf, s390x and ppc64le, and
ahead of Ubuntu's own `docker.io` package. The repository setup is the one
Docker's install page gives:

```sh
sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"
```

The `usermod` line lets the lab user run `docker` without `sudo` after the
next login, which `lab/lab.sh` expects. Docker Desktop for Linux is a
different product that runs its engine in a virtual machine under KVM,
the Linux kernel's hypervisor, so it needs nested virtualization enabled
for the VM. The Engine is what the lab uses.

### Docker Desktop on Windows

```powershell
winget install --id Docker.DockerDesktop -e --accept-package-agreements --accept-source-agreements
```

The winget package is Docker's own installer, with x64 and ARM64 builds.
Docker Desktop for Windows on Arm is an early-access build that supports
the WSL 2 backend only, with no Windows containers. Both need:

- Windows 11 Pro, Enterprise or Education, version 23H2 (build 22631) or
  later;
- WSL version 2.1.5 or later with the WSL 2 feature turned on;
- 8 GB of system memory;
- hardware virtualization available to Windows, which inside a VM is
  nested virtualization.

In a Windows VM without nested virtualization the install itself
succeeds, WSL 2 cannot start and Docker Desktop's engine never comes up,
so on such a host it is left out of the Windows snapshot.

### Docker Desktop on macOS

```sh
brew install --cask docker-desktop
```

The cask installs Docker's own build for the Mac's architecture and
needs:

- macOS 14 or later: Docker supports the current major release and the
  two before it;
- 4 GB of memory;
- Rosetta 2 only for a few optional command-line tools and for running
  amd64 images, installed with `softwareupdate --install-rosetta`;
- the Virtualization framework, which inside a VM is nested
  virtualization.

In a macOS VM without nested virtualization the engine cannot start;
OrbStack and Colima use the same framework and fail the same way. On
such a host it is left out of the macOS snapshot, and a macOS agent that
needs a container is exercised on a Mac that is not a VM.

## Versions

The builds in the snapshots and the ids that pin them. Each is the
vendor's current stable or long-term support release, checked against the
release pages and the package indexes on 2026-10-23, the Python line on
2026-10-25.

| Tool | Windows (winget id) | macOS (Homebrew) | Line |
| --- | --- | --- | --- |
| Python | `Python.PythonInstallManager` 26.4, then `py install 3.15` 3.15.1 | `python@3.15` 3.15.1 | 3.15, the current release since 2026-10-09, on Windows and macOS; 3.14 on Ubuntu, the `python3` of 26.04's archive |
| Git | `Git.Git` 2.55 | `git` 2.56 | current |
| GitHub CLI | `GitHub.cli` 2.103 | `gh` 2.103 | current |
| Node | `OpenJS.NodeJS.LTS` 24.22 | `node@24` 24.22 | LTS; Node 26 becomes LTS on 2026-10-28, after which `OpenJS.NodeJS.LTS` moves to it |
| VS Code | `Microsoft.VisualStudioCode` 1.142 | `visual-studio-code` 1.143 | current |
| Visual Studio Build Tools | `Microsoft.VisualStudio.BuildTools` 18.11 | not needed | 2026 |
| Rust | `Rustlang.Rustup` 1.29 | `rustup` 1.29 | stable toolchain |
| Go | `GoLang.Go` 1.27 | `go` 1.27 | current |
| Ruby | `RubyInstallerTeam.RubyWithDevKit.4.0` 4.0.7 | `ruby` 4.0.9 | 4.0 |
| OpenJDK | `Microsoft.OpenJDK.25` 25.0.4 | `openjdk@25` 25.0.5 | LTS |
| PowerShell | `Microsoft.PowerShell` 7.6.8 | `powershell` 7.6.8 | 7.6, the LTS line until November 2028; 7.4 LTS ends 2026-11-10 |
| uv | `astral-sh.uv` 0.13 | `uv` 0.13 | current |
| pipx | pip, 1.18 | `pipx` 1.18 | current |
| Docker Desktop | `Docker.DockerDesktop` 4.96.3 | `docker-desktop` 4.96.3 | current; only on a host with nested virtualization |
| Docker Engine | not available | not available | 29.9 on Ubuntu, from Docker's apt repository |

A rebuild of a snapshot checks the current versions first: a line that
has moved (Node's LTS, Java's LTS, a PowerShell line reaching the end of
support) changes the id to install, not only the number.
