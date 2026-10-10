"""Root causes per performance subtopic, each tagged with the level it belongs to.

One symptom can have several causes, so the trainee has to investigate instead of recognising the
question. "basis" causes are classics that the standard commands show clearly; "gemiddeld" causes
mislead the obvious first signal or need a less common command. "trading" marks causes typical for
low-latency trading hosts; from "gemiddeld" on they are preferred.
"""

import random

CAUSES = {
    "use_methode": [
        {"id": "cpu_saturation", "level": "basis", "trading": False,
         "cause": "A runaway process saturates the CPUs: the run queue stays well above the core count."},
        {"id": "memory_swapping", "level": "basis", "trading": False,
         "cause": "A process has grown until the host swaps: available memory is near zero and pages are swapped in and out."},
        {"id": "disk_saturation", "level": "basis", "trading": False,
         "cause": "A batch job saturates the disk the application uses: %util is 100 and the request queue is deep."},
        {"id": "nic_errors", "level": "gemiddeld", "trading": True,
         "cause": "A faulty optic causes receive errors (CRC) on the exchange-facing NIC; utilization is low, the errors dimension is what is wrong."},
        {"id": "fd_exhaustion", "level": "gemiddeld", "trading": False,
         "cause": "The application hits its open-files limit (ulimit nofile) and new connections fail with 'Too many open files' — a software resource, not hardware."},
        {"id": "memcg_limit", "level": "gemiddeld", "trading": False,
         "cause": "A container runs at its memory cgroup limit: the kernel keeps reclaiming its page cache and occasionally OOM-kills a worker, while the host has plenty of free memory."},
    ],
    "checklist_60s": [
        {"id": "oom_killer", "level": "basis", "trading": False,
         "cause": "The OOM killer killed the service, systemd restarted it, and it is slow while it warms up again; dmesg shows the kill."},
        {"id": "runaway_process", "level": "basis", "trading": False,
         "cause": "A runaway process uses all CPUs, so the service competes for CPU time."},
        {"id": "swapping", "level": "basis", "trading": False,
         "cause": "The host is swapping because a second application was started on it; free shows little available memory and vmstat shows si/so."},
        {"id": "single_core_bottleneck", "level": "gemiddeld", "trading": True,
         "cause": "The service's single-threaded event loop is pinned to one core at 100% while the other cores are idle, so total CPU looks low."},
        {"id": "link_saturation", "level": "gemiddeld", "trading": False,
         "cause": "A replication job saturates the network link the service uses; sar -n DEV shows throughput at line rate."},
        {"id": "tcp_retransmits", "level": "gemiddeld", "trading": True,
         "cause": "Packet loss on the path to a dependency causes TCP retransmits; CPU, memory and disk are all fine, only sar -n TCP,ETCP shows it."},
    ],
    "load_vs_cpu": [
        {"id": "runaway_cpu", "level": "basis", "trading": False,
         "cause": "A runaway process keeps the run queue above the core count: high load with high user CPU."},
        {"id": "disk_dstate", "level": "basis", "trading": False,
         "cause": "Tasks block in D state on a saturated local disk: high load while the CPUs are mostly idle and iowait is high."},
        {"id": "hung_nfs", "level": "gemiddeld", "trading": False,
         "cause": "An NFS mount has hung: processes touching it sit in D state, but the local disks are quiet, so iostat shows nothing."},
        {"id": "fork_storm", "level": "gemiddeld", "trading": False,
         "cause": "A misbehaving health-check script spawns hundreds of short-lived processes per second: high load and system CPU, but no single process stands out in top."},
        {"id": "memory_reclaim", "level": "gemiddeld", "trading": False,
         "cause": "Memory pressure makes tasks stall in direct reclaim and swap-in: load and iowait rise, but the cause is memory, not the disk workload."},
    ],
    "io_wait_en_dstate": [
        {"id": "backup_shared_disk", "level": "basis", "trading": True,
         "cause": "A backup or compression job saturates the disk that also holds the application's journal, so its fsync calls block in D state."},
        {"id": "debug_logging", "level": "basis", "trading": False,
         "cause": "A config change set logging to debug with synchronous writes, and the application's own log writes saturate the disk."},
        {"id": "failing_disk", "level": "gemiddeld", "trading": False,
         "cause": "A failing disk retries reads and writes: very high await with low throughput, and I/O errors in dmesg."},
        {"id": "hung_nfs", "level": "gemiddeld", "trading": False,
         "cause": "The application writes to an NFS mount that has become unresponsive: processes in D state with an NFS wait channel, local disks idle."},
        {"id": "writeback_storm", "level": "gemiddeld", "trading": False,
         "cause": "A large file written to page cache builds up dirty pages; when writeback flushes them, the application's fsync blocks for seconds at a time."},
        {"id": "swap_pagein", "level": "gemiddeld", "trading": False,
         "cause": "The application's memory was swapped out; touching it causes page-ins from the swap disk, which looks like disk I/O wait."},
    ],
    "latency_en_context_switches": [
        {"id": "noisy_neighbour", "level": "basis", "trading": True,
         "cause": "A batch job scheduled on the same cores preempts the trading process: its involuntary context switches rise sharply."},
        {"id": "too_many_threads", "level": "basis", "trading": False,
         "cause": "A misconfigured thread pool runs hundreds of threads on a few cores, so the scheduler keeps switching between them."},
        {"id": "cfs_throttling", "level": "gemiddeld", "trading": True,
         "cause": "The pod's CPU limit makes the CFS quota throttle it in bursts; the host is idle, but nr_throttled in the cgroup's cpu.stat keeps rising."},
        {"id": "irq_on_trading_core", "level": "gemiddeld", "trading": True,
         "cause": "NIC interrupts were moved onto the core running the trading thread, so softirq work preempts it (%soft high on that one core)."},
        {"id": "cpu_power_states", "level": "gemiddeld", "trading": True,
         "cause": "A tuned profile reset after a kernel update put the CPU governor on powersave with deep C-states, so cores wake slowly after idle periods."},
        {"id": "lock_contention", "level": "gemiddeld", "trading": False,
         "cause": "Threads contend on one lock: voluntary context switches are high while CPU usage stays low."},
        {"id": "numa_mismatch", "level": "gemiddeld", "trading": True,
         "cause": "After a restart the trading process landed on the other CPU socket than the NIC and its memory, so every packet and allocation crosses the socket interconnect (numastat shows remote node memory)."},
        {"id": "thp_compaction", "level": "gemiddeld", "trading": True,
         "cause": "Transparent huge pages were re-enabled by an OS update; khugepaged and memory compaction stall the trading process for milliseconds at random moments."},
        {"id": "kernel_bypass_fallback", "level": "gemiddeld", "trading": True,
         "cause": "After an upgrade the kernel-bypass library (Onload) no longer accelerates the order socket and silently falls back to the kernel stack, so latency rises from microseconds to tens of microseconds while everything still works."},
    ],
    "netwerk_retransmits_drops": [
        {"id": "link_saturation", "level": "basis", "trading": True,
         "cause": "A backup sends over the same NIC as the order traffic and saturates it, causing drops and retransmits."},
        {"id": "bad_cable", "level": "basis", "trading": True,
         "cause": "A faulty cable or optic causes CRC errors on receive, visible in ip -s link and ethtool -S."},
        {"id": "small_rx_ring", "level": "gemiddeld", "trading": True,
         "cause": "The NIC's RX ring is too small for market-data microbursts, so the NIC drops packets (missed / no-buffer counters) while the link is far from full."},
        {"id": "socket_buffer", "level": "gemiddeld", "trading": True,
         "cause": "The application reads its socket too slowly and the receive buffer is too small; netstat -s shows receive buffer errors and pruned packets."},
        {"id": "mtu_mismatch", "level": "gemiddeld", "trading": True,
         "cause": "An MTU change on one side means large packets are dropped while small ones pass, so only big messages stall."},
        {"id": "conntrack_full", "level": "gemiddeld", "trading": False,
         "cause": "The conntrack table is full, so the kernel drops packets of new connections; dmesg shows 'nf_conntrack: table full, dropping packet'."},
        {"id": "multicast_gap", "level": "gemiddeld", "trading": True,
         "cause": "Multicast market data has gaps because reverse path filtering (rp_filter) drops packets arriving on the second feed interface after a routing change; UDP has no retransmit, so the order book goes stale."},
    ],
    # Kubernetes investigations. "scope" says where the cause lives: in the pod, on one node, or in
    # something every node shares. Finding that out first is what these scenarios train.
    "k8s_cluster": [
        {"id": "oom_killed", "level": "basis", "trading": True, "scope": "pod",
         "cause": "One order-gateway pod is OOMKilled every 20 minutes or so: its memory limit (2Gi) is below what it "
                  "needs at peak load. It restarts, and orders routed to it fail during the restart."},
        {"id": "crashloop_config", "level": "basis", "trading": True, "scope": "pod",
         "cause": "After this morning's deploy the new market-data handler pods crash on start (CrashLoopBackOff): the "
                  "environment variable EXCHANGE_URL is missing from the new ConfigMap. The old ReplicaSet still "
                  "serves part of the traffic."},
        {"id": "image_pull", "level": "basis", "trading": False, "scope": "pod",
         "cause": "A rollout is stuck: the new pods are in ImagePullBackOff because the image tag in the Deployment "
                  "does not exist. The old pods still run, so the gateway has less capacity than planned."},
        {"id": "disk_pressure", "level": "basis", "trading": False, "scope": "node",
         "cause": "One node's disk is full of container logs (DiskPressure=True). The kubelet evicts pods from that "
                  "node, including gateway pods, and they restart elsewhere."},
        {"id": "noisy_neighbour_disk", "level": "basis", "trading": True, "scope": "node",
         "cause": "A backup CronJob pod without resource limits runs on one node and saturates its disk. The gateway "
                  "pods on that node are slow; the replicas on the other nodes are fine."},
        {"id": "cpu_throttling", "level": "gemiddeld", "trading": True, "scope": "pod",
         "cause": "The order-gateway pods have a CPU limit of 2 cores. In bursts the CFS quota throttles them "
                  "(nr_throttled in cpu.stat rises), causing latency spikes while the nodes themselves are mostly idle."},
        {"id": "liveness_too_strict", "level": "gemiddeld", "trading": True, "scope": "pod",
         "cause": "The gateway's liveness probe has a 1-second timeout. Under load at the market open the health "
                  "endpoint answers slower, so the kubelet kills and restarts healthy pods (Events: Liveness probe "
                  "failed), leaving gaps in order flow."},
        {"id": "readiness_failing", "level": "gemiddeld", "trading": True, "scope": "pod",
         "cause": "Two of the four gateway pods fail their readiness probe because its dependency check times out. "
                  "They are removed from the Service endpoints, so the remaining two pods take all traffic and are overloaded."},
        {"id": "node_nic_drops", "level": "gemiddeld", "trading": True, "scope": "node",
         "cause": "On one node the NIC to the exchange overflows its receive ring during market-data bursts (RX missed "
                  "rises on the node). Pods on that node see retransmits and late acks; pods on other nodes are fine."},
        {"id": "node_memory_pressure", "level": "gemiddeld", "trading": False, "scope": "node",
         "cause": "One node is overcommitted: pods without memory limits push it into memory pressure "
                  "(MemoryPressure=True), and the kernel OOM-kills processes in several pods on that node."},
        {"id": "kubelet_down", "level": "gemiddeld", "trading": False, "scope": "node",
         "cause": "One node went NotReady because its kubelet stopped after its client certificate expired. Its pods "
                  "are marked Unknown and only get replaced elsewhere after the eviction timeout."},
        {"id": "coredns_overloaded", "level": "gemiddeld", "trading": True, "scope": "shared",
         "cause": "CoreDNS runs a single, CPU-limited replica and is overloaded. Pods on every node see intermittent "
                  "DNS timeouts when resolving the exchange hostname, so new connections fail now and then."},
    ],
}


# The performance subtopics: their investigations run on a single Linux host (a VM).
VM_INVESTIGATION_SUBTOPICS = [subtopic for subtopic in CAUSES if subtopic != "k8s_cluster"]


def pick_cause(subtopic: str, level: str, recent_ids: list[str]) -> dict | None:
    """Pick a cause for the level, skipping recently used ones; trading causes weigh double from gemiddeld on."""
    pool = [c for c in CAUSES.get(subtopic, []) if level == "gemiddeld" or c["level"] == "basis"]
    if not pool:
        return None
    fresh = [c for c in pool if c["id"] not in recent_ids] or pool
    weights = [2 if level == "gemiddeld" and c["trading"] else 1 for c in fresh]
    return random.choices(fresh, weights=weights)[0]
