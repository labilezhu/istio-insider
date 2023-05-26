
## Setup lldb
```bash
apt install python3-lldb
```
## Other

```
Envoy::Event::FileEventImpl::mergeInjectedEventsAndRunCb(unsigned int) (/work/bazel-work/external/envoy/source/common/event/file_event_impl.cc:161)
Envoy::Event::FileEventImpl::assignEvents(unsigned int, event_base*)::$_1::operator()(int, short, void*) const (/work/bazel-work/external/envoy/source/common/event/file_event_impl.cc:82)
Envoy::Event::FileEventImpl::assignEvents(unsigned int, event_base*)::$_1::__invoke(int, short, void*) (/work/bazel-work/external/envoy/source/common/event/file_event_impl.cc:66)
event_persist_closure (/work/bazel-work/external/com_github_libevent_libevent/event.c:1645)
event_process_active_single_queue (/work/bazel-work/external/com_github_libevent_libevent/event.c:1704)
event_process_active (/work/bazel-work/external/com_github_libevent_libevent/event.c:1805)
event_base_loop (/work/bazel-work/external/com_github_libevent_libevent/event.c:2047)
Envoy::Event::LibeventScheduler::run(Envoy::Event::Dispatcher::RunType) (/work/bazel-work/external/envoy/source/common/event/libevent_scheduler.cc:60)
Envoy::Event::DispatcherImpl::run(Envoy::Event::Dispatcher::RunType) (/work/bazel-work/external/envoy/source/common/event/dispatcher_impl.cc:299)
Envoy::Server::WorkerImpl::threadRoutine(Envoy::Server::GuardDog&, std::__1::function<void ()> const&) (/work/bazel-work/external/envoy/source/server/worker_impl.cc:144)
Envoy::Server::WorkerImpl::start(Envoy::Server::GuardDog&, std::__1::function<void ()> const&)::$_6::operator()() const (/work/bazel-work/external/envoy/source/server/worker_impl.cc:111)
decltype(std::__1::forward<Envoy::Server::WorkerImpl::start(Envoy::Server::GuardDog&, std::__1::function<void ()> const&)::$_6&>(fp)()) std::__1::__invoke<Envoy::Server::WorkerImpl::start(Envoy::Server::GuardDog&, std::__1::function<void ()> const&)::$_6&>(Envoy::Server::WorkerImpl::start(Envoy::Server::GuardDog&, std::__1::function<void ()> const&)::$_6&) (@decltype(std::__1::forward<Envoy::Server::WorkerImpl::start(Envoy::Server::GuardDog&, std::__1::function<void ()> const&)::$_6&>(fp)()) std::__1::__invoke<Envoy::Server::WorkerImpl::start(Envoy::Server::GuardDog&, std::__1::function<void ()> const&)::$_6&>(Envoy::Server::WorkerImpl::start(Envoy::Server::GuardDog&, std::__1::function<void ()> const&)::$_6&):11)
void std::__1::__invoke_void_return_wrapper<void, true>::__call<Envoy::Server::WorkerImpl::start(Envoy::Server::GuardDog&, std::__1::function<void ()> const&)::$_6&>(Envoy::Server::WorkerImpl::start(Envoy::Server::GuardDog&, std::__1::function<void ()> const&)::$_6&) (@void std::__1::__invoke_void_return_wrapper<void, true>::__call<Envoy::Server::WorkerImpl::start(Envoy::Server::GuardDog&, std::__1::function<void ()> const&)::$_6&>(Envoy::Server::WorkerImpl::start(Envoy::Server::GuardDog&, std::__1::function<void ()> const&)::$_6&):11)
std::__1::__function::__alloc_func<Envoy::Server::WorkerImpl::start(Envoy::Server::GuardDog&, std::__1::function<void ()> const&)::$_6, std::__1::allocator<Envoy::Server::WorkerImpl::start(Envoy::Server::GuardDog&, std::__1::function<void ()> const&)::$_6>, void ()>::operator()() (@std::__1::__function::__alloc_func<Envoy::Server::WorkerImpl::start(Envoy::Server::GuardDog&, std::__1::function<void ()> const&)::$_6, std::__1::allocator<Envoy::Server::WorkerImpl::start(Envoy::Server::GuardDog&, std::__1::function<void ()> const&)::$_6>, void ()>::operator()():11)
std::__1::__function::__func<Envoy::Server::WorkerImpl::start(Envoy::Server::GuardDog&, std::__1::function<void ()> const&)::$_6, std::__1::allocator<Envoy::Server::WorkerImpl::start(Envoy::Server::GuardDog&, std::__1::function<void ()> const&)::$_6>, void ()>::operator()() (@std::__1::__function::__func<Envoy::Server::WorkerImpl::start(Envoy::Server::GuardDog&, std::__1::function<void ()> const&)::$_6, std::__1::allocator<Envoy::Server::WorkerImpl::start(Envoy::Server::GuardDog&, std::__1::function<void ()> const&)::$_6>, void ()>::operator()():10)
std::__1::__function::__value_func<void ()>::operator()() const (@std::__1::__function::__value_func<void ()>::operator()() const:16)
std::__1::function<void ()>::operator()() const (@std::__1::function<void ()>::operator()() const:9)
Envoy::Thread::ThreadImplPosix::ThreadImplPosix(std::__1::function<void ()>, absl::optional<Envoy::Thread::Options> const&)::'lambda'(void*)::operator()(void*) const (/work/bazel-work/external/envoy/source/common/common/posix/thread_impl.cc:49)
Envoy::Thread::ThreadImplPosix::ThreadImplPosix(std::__1::function<void ()>, absl::optional<Envoy::Thread::Options> const&)::'lambda'(void*)::__invoke(void*) (/work/bazel-work/external/envoy/source/common/common/posix/thread_impl.cc:48)
start_thread (@start_thread:162)
__clone3 (@__clone3:20)
```

```
image lookup --address 0x55cabab61b80 --verbose

image list
[  0] 61D5E8E1 0x000055caab75c000 /work/bazel-out/k8-dbg/bin/envoy 
```

```log
➜  ~ sudo pmap -X $PID  
119225:   /usr/local/bin/envoy -c etc/istio/proxy/envoy-rev.json --drain-time-s 45 --drain-strategy immediate --local-address-ip-version v4 --file-flush-interval-msec 1000 --disable-hot-restart --allow-unknown-static-fields --log-format %Y-%m-%dT%T.%fZ?%l?envoy %n %g:%#?%v?thread=%t -l warning --component-log-level misc:error --concurrency 2
         Address Perm   Offset Device  Inode   Size    Rss    Pss Referenced Anonymous LazyFree ShmemPmdMapped FilePmdMapped Shared_Hugetlb Private_Hugetlb Swap SwapPss Locked THPeligible Mapping
    555555554000 r--p 00000000  00:b8 263474  74504  18672  18672      18672         4        0              0             0              0               0    0       0      0           0 envoy
    555559e17000 r-xp 048c2000  00:b8 263474 137616  81424  81424      81424        36        0              0             0              0               0    0       0      0           0 envoy
    55556247b000 r--p 0cf25000  00:b8 263474   3008   3008   3008       3008      3008        0              0             0              0               0    0       0      0           0 envoy
    55556276c000 rw-p 0d215000  00:b8 263474    424    408    408        408       408        0              0             0              0               0    0       0      0           0 envoy
    5555627d6000 rw-p 00000000  00:00      0  24072  17156  17156      17156     17156        0              0             0              0               0    0       0      0           0 [heap]
```

```
sudo less /proc/$PID/smaps

555555554000-555559e16000 r--p 00000000 00:b8 263474                     /usr/local/bin/envoy
Size:              74504 kB
KernelPageSize:        4 kB

555559e17000-55556247b000 r-xp 048c2000 00:b8 263474                     /usr/local/bin/envoy
Size:             137616 kB

55556247b000-55556276b000 r--p 0cf25000 00:b8 263474                     /usr/local/bin/envoy
Size:               3008 kB

55556276c000-5555627d6000 rw-p 0d215000 00:b8 263474                     /usr/local/bin/envoy
Size:                424 kB

5555627d6000-555563f58000 rw-p 00000000 00:00 0                          [heap]
Size:              24072 kB

```

## breakpoint

```
breakpoint modify -T wrk:worker_0  12 

breakpoint command add -s python -o 'frame.thread.name != "envoy"' 21
breakpoint command add -s python -o 'print("frame.thread.name = {}".format( frame.thread.name ))' 21

breakpoint command add -s python -o 'frame.thread.name != "envoy"' 21 27 28 29 30

expr -l python -- 'return frame.thread.name != "envoy"'

breakpoint modify -T wrk:worker_0  12 

breakpoint modify -c wrk:worker_0  12 
```

```python
breakpoint command add -s python 19
print('frame.thread.name = {}'.format( frame.thread.name ))
return frame.thread.name != "envoy"
DONE
```

## randomize_va_space

```bash
# to disable it, run```
echo 0 | sudo tee /proc/sys/kernel/randomize_va_space
cat /proc/sys/kernel/randomize_va_space
#or 
sudo sysctl kernel.randomize_va_space=0 

# to enable it again, run
echo 2 | sudo tee /proc/sys/kernel/randomize_va_space

# so you'll have to configure this in sysctl. Add a file /etc/sysctl.d/01-disable-aslr.conf containing:

kernel.randomize_va_space = 0
```