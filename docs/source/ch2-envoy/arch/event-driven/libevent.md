# libevent 核心思想

`libevent` 的有两个重要的概念： `event_base` 、`event` 。


![](libevent.assets/libevent.drawio.svg)


## event
event 这个词意义大广大，libevent 中的 `event` 对象，到底是什么意思？ 理解 OOP 方法编写的某个对象的功能或定位，有一个窍门，就是看对象的属性名和方法名。从上图看了， `event` 是指在某个 fd(file descriptor 文件描述符/句柄) 上可能会发生的信号，如 Read Ready 、 Write Ready 等等。 注意，这里是可能会发生的事件，包括：未来可能发生、正在发生、曾经发生过的事件。

应用可能对 `event` 进行很多操作，包括监听或订阅事件，以在事件真正发生后，可以 callback 到应用代码。

## event_base

可以认为是 `event` 的集合。多数事件驱动型的应用实现，每个工作线程拥有自己的 `event_base` 。并执行自己的 `event_base`的事件循环，包括 Envoy 。

> http://www.wangafu.net/~nickm/libevent-book/Ref2_eventbase.html

* event_base - `event_base` structures. Each `event_base` structure holds a set of events and can poll to determine which events are active.

If an event_base is set up to use locking, it is safe to access it between multiple threads. Its loop can only be run in a single thread, however. If you want to have multiple threads polling for IO, you need to have an `event_base` for each thread.

Each event_base has a "`method`", or a backend that it uses to determine which events are ready. The recognized `methods` are:

- select
- poll
- epoll
- kqueue
- devpoll
- evport
- win32



### Setting up a default event_base

The `event_base_new()` function allocates and returns a new event base with the default settings. It examines the environment variables and returns a pointer to a new `event_base`. If there is an error, it returns NULL.

```c
struct event_base *event_base_new(void);
```

## event loop

### function

```c
Interface
#define EVLOOP_ONCE             0x01
#define EVLOOP_NONBLOCK         0x02
#define EVLOOP_NO_EXIT_ON_EMPTY 0x04

int event_base_loop(struct event_base *base, int flags);
```

> http://www.wangafu.net/~nickm/libevent-book/Ref3_eventloop.html

By default, the `event_base_loop()` function runs an event_base until there are no more events registered in it. To run the loop, it repeatedly checks whether any of the registered events has triggered (for example, if a read event’s file descriptor is ready to read, or if a timeout event’s timeout is ready to expire). Once this happens, it marks all triggered events as "`active`", and starts to run them.

#### flags

You can change the behavior of `event_base_loop()` by setting one or more flags in its flags argument. 

- `EVLOOP_ONCE` , then the loop will wait until some events become `active`, then run `active` events until there are no more to run, then return. 
- `EVLOOP_NONBLOCK` , then the loop will not wait for events to trigger: it will only check whether any events are ready to trigger immediately, and run their callbacks if so.
- `EVLOOP_NO_EXIT_ON_EMPTY` 
- default, function runs an event_base until there are no more events registered in it.

Ordinarily, the loop will exit as soon as it has no `pending` or `active` events. You can override this behavior by passing the `EVLOOP_NO_EXIT_ON_EMPTY` flag---for example, if you’re going to be adding events from some other thread. If you do set `EVLOOP_NO_EXIT_ON_EMPTY`, the loop will keep running until somebody calls `event_base_loopbreak()`, or calls `event_base_loopexit()`, or an error occurs. 

#### returns

When it is done, `event_base_loop()` returns :

* 0 if it exited normally, 
* -1 if it exited because of some unhandled error in the backend, and 
* 1 if it exited because there were no more pending or active events.

### Pseudocode

```c
while (any events are registered with the loop,
        or EVLOOP_NO_EXIT_ON_EMPTY was set) {

    if (EVLOOP_NONBLOCK was set, or any events are already active)
        If any registered events have triggered, mark them active.
    else
        Wait until at least one event has triggered, and mark it active.

    for (p = 0; p < n_priorities; ++p) {
       if (any event with priority of p is active) {
          Run all active events with priority of p.
          break; /* Do not run any events of a less important priority */
       }
    }

    if (EVLOOP_ONCE was set or EVLOOP_NONBLOCK was set)
       break;
}
```

### internal time cache

```c
int event_base_gettimeofday_cached(struct event_base *base,
    struct timeval *tv_out);
```

```c
int event_base_update_cache_time(struct event_base *base);
```

### Dumping the event_base status

```c
void event_base_dump_events(struct event_base *base, FILE *f);
```

For help debugging your program (or debugging Libevent!) you might sometimes want a complete list of all events added in the event_base and their status. Calling event_base_dump_events() writes this list to the stdio file provided.

The list is meant to be human-readable; its format will change in future versions of Libevent.


### Running a function over every event in an event_base

```c
typedef int (*event_base_foreach_event_cb)(const struct event_base *,
    const struct event *, void *);

int event_base_foreach_event(struct event_base *base,
                             event_base_foreach_event_cb fn,
                             void *arg);
```

You can use `event_base_foreach_event()` to iterate over every currently active or pending event associated with an `event_base()`. The provided callback will be invoked exactly once per event, **in an unspecified order**. The third argument of event_base_foreach_event() will be passed as the third argument to each invocation of the callback.

The callback function must return 0 to continue iteration, or some other integer to stop iterating. Whatever value the callback function finally returns will then be returned by `event_base_foreach_function()`.

Your **callback function must not modify any of the events that it receives, or add or remove any events to the event base, or otherwise modify any event associated with the event base**, or undefined behavior can occur, up to or including crashes and heap-smashing.

The `event_base` lock will be held for the duration of the call to `event_base_foreach_event()` — this will block other threads from doing anything useful with the event_base, so make sure that your callback doesn’t take a long time.





## Working with events

> http://www.wangafu.net/~nickm/libevent-book/Ref4_event.html

Libevent’s basic unit of operation is the _`event`_. Every event represents a set of conditions, including:

- A file descriptor being ready to read from or write to.

- A file descriptor _becoming_ ready to read from or write to (Edge-triggered IO only).

- A timeout expiring.

- A signal occurring.

- A user-triggered event.

### event state

- `initialized`
- `pending`
- `active`

Events have similar lifecycles:

1. Once you call a Libevent function to set up an event and associate it with an event base, it becomes **initialized**. 
2. At this point, you can _add_, which makes it **pending** in the base. When the event is pending, 
3. if the conditions that would trigger an event occur (e.g., its file descriptor changes state or its timeout expires), the event becomes **active**, and its (user-provided) callback function is run. 
4. If the event is configured **persistent**, it remains **pending**. 
5. If it is not persistent, it stops being **pending** when its callback runs. 
6. You can make a pending event non-pending by _deleting_ it, and you can _add_ a non-pending event to make it pending again.



![libevent-6-事件状态图.png](./libevent.assets/1538970316042-d588bff5-1f5f-4f49-ad6a-e078ba0f9df9.png)

[Libevent状态转换图 from https://developer.aliyun.com/article/659277#fromHistory]



### Constructing event objects

To create a new event, use the `event_new()` interface.

```c
typedef void (*event_callback_fn)(evutil_socket_t fd, short what, void * args);

struct event *event_new(struct event_base *base, evutil_socket_t fd,
    short what, event_callback_fn cb,
    void *arg);

// what:
#define EV_TIMEOUT      0x01
#define EV_READ         0x02
#define EV_WRITE        0x04
#define EV_SIGNAL       0x08
#define EV_PERSIST      0x10
#define EV_ET           0x20

void event_free(struct event *event);
```

#### example

```c
#include <event2/event.h>

void cb_func(evutil_socket_t fd, short what, void *arg)
{
        const char *data = arg;
        printf("Got an event on socket %d:%s%s%s%s [%s]",
            (int) fd,
            (what&EV_TIMEOUT) ? " timeout" : "",
            (what&EV_READ)    ? " read" : "",
            (what&EV_WRITE)   ? " write" : "",
            (what&EV_SIGNAL)  ? " signal" : "",
            data);
}

void main_loop(evutil_socket_t fd1, evutil_socket_t fd2)
{
        struct event *ev1, *ev2;
        struct timeval five_seconds = {5,0};
        struct event_base *base = event_base_new();

        /* The caller has already set up fd1, fd2 somehow, and make them
           nonblocking. */

        ev1 = event_new(base, fd1, EV_TIMEOUT|EV_READ|EV_PERSIST, cb_func,
           (char*)"Reading event");
        ev2 = event_new(base, fd2, EV_WRITE|EV_PERSIST, cb_func,
           (char*)"Writing event");

        event_add(ev1, &five_seconds);
        event_add(ev2, NULL);
        event_base_dispatch(base);
}
```

#### event flags

- EV_TIMEOUT
  This flag indicates an event that becomes active after a timeout elapses.
  The EV_TIMEOUT flag is ignored when constructing an event: you
  can either set a timeout when you add the event, or not.  It is
  set in the 'what' argument to the callback function when a timeout
  has occurred.

- EV_READ
  This flag indicates an event that becomes active when the provided file descriptor is ready for reading.

- EV_WRITE
  This flag indicates an event that becomes active when the provided file descriptor is ready for writing.

- EV_SIGNAL
  Used to implement signal detection. See "Constructing signal events" below.

- EV_PERSIST
  Indicates that the event is persistent. See "About Event Persistence" below.

- EV_ET
  Indicates that the event should be edge-triggered, if the underlying event_base backend supports edge-triggered events. This affects the semantics of EV_READ and EV_WRITE.

#### callback argument

Frequently, you might want to create an event that receives itself as a callback argument. You can’t just pass a pointer to the event as an argument to event_new(), though, because it does not exist yet. To solve this problem, you can use event_self_cbarg().

example:

```c
#include <event2/event.h>

static int n_calls = 0;

void cb_func(evutil_socket_t fd, short what, void *arg)
{
    struct event *me = arg;

    printf("cb_func called %d times so far.\n", ++n_calls);

    if (n_calls > 100)
       event_del(me);
}

void run(struct event_base *base)
{
    struct timeval one_sec = { 1, 0 };
    struct event *ev;
    /* We're going to set up a repeating timer to get called called 100
       times. */
    ev = event_new(base, -1, EV_PERSIST, cb_func, event_self_cbarg());
    event_add(ev, &one_sec);
    event_base_dispatch(base);
}
```




#### About Event Persistence

By default, whenever a pending event becomes active (because its fd is ready to read or write, or because its timeout expires), it becomes non-pending right before its callback is executed. Thus, if you want to make the event pending again, you can call event_add() on it again from inside the callback function.

If the EV_PERSIST flag is set on an event, however, the event is persistent. This means that event remains pending even when its callback is activated. If you want to make it non-pending from within its callback, you can call event_del() on it.

The timeout on a persistent event resets whenever the event’s callback runs. Thus, if you have an event with flags EV_READ|EV_PERSIST and a timeout of five seconds, the event will become active:

- Whenever the socket is ready for reading.

- Whenever five seconds have passed since the event last became active.

#### Constructing signal events

```c
struct event *hup_event;
struct event_base *base = event_base_new();

/* call sighup_function on a HUP signal */
hup_event = evsignal_new(base, SIGHUP, sighup_function, NULL);
```

Note that signal callbacks are run in the event loop after the signal occurs, so it is safe for them to call functions that you are not supposed to call from a regular POSIX signal handler.

### Making events pending and non-pending

Once you have constructed an event, it won’t actually do anything until you have made it pending by adding it. You do this with event_add:

```c
int event_add(struct event *ev, const struct timeval *tv);

int event_del(struct event *ev);

```

### Events with priorities

```c
int event_priority_set(struct event *event, int priority);
```

### Finding the currently running event

```c
struct event *event_base_get_running_event(struct event_base *base);
```

### Inspecting event status

```c
int event_pending(const struct event *ev, short what, struct timeval *tv_out);

#define event_get_signal(ev) /* ... */
evutil_socket_t event_get_fd(const struct event *ev);
struct event_base *event_get_base(const struct event *ev);
short event_get_events(const struct event *ev);
event_callback_fn event_get_callback(const struct event *ev);
void *event_get_callback_arg(const struct event *ev);
int event_get_priority(const struct event *ev);

void event_get_assignment(const struct event *event,
        struct event_base **base_out,
        evutil_socket_t *fd_out,
        short *events_out,
        event_callback_fn *callback_out,
        void **arg_out);
```

### Manually activating an event

```c
void event_active(struct event *ev, int what, short ncalls);
```

This function makes an event ev become active with the flags what (a combination of EV_READ, EV_WRITE, and EV_TIMEOUT). The event does not need to have previously been pending, and activating it does not make it pending.

Warning: calling event_active() recursively on the same event may result in resource exhaustion. 



