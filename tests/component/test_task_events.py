import pytest

import nidaqmx
from nidaqmx.constants import EveryNSamplesEventType, Signal
from nidaqmx.error_codes import DAQmxErrors
from tests._event_utils import (
    DoneEventObserver,
    EveryNSamplesEventObserver,
    SignalEventObserver,
)


@pytest.fixture
def ai_task(task: nidaqmx.Task, any_x_series_device: nidaqmx.system.Device) -> nidaqmx.Task:
    task.ai_channels.add_ai_voltage_chan(any_x_series_device.ai_physical_chans[0].name)
    return task


@pytest.fixture
def ai_task_with_real_device(
    task: nidaqmx.Task, real_x_series_device: nidaqmx.system.Device
) -> nidaqmx.Task:
    task.ai_channels.add_ai_voltage_chan(real_x_series_device.ai_physical_chans[0].name)
    return task


@pytest.fixture
def ao_task(task: nidaqmx.Task, any_x_series_device: nidaqmx.system.Device) -> nidaqmx.Task:
    task.ao_channels.add_ao_voltage_chan(any_x_series_device.ao_physical_chans[0].name)
    return task


@pytest.mark.library_only
def test___done_event_registered___run_finite_acquisition___callback_invoked_once_with_success_status(
    ai_task: nidaqmx.Task,
) -> None:
    event_observer = DoneEventObserver()
    ai_task.register_done_event(event_observer.handle_done_event)
    ai_task.timing.cfg_samp_clk_timing(rate=10000.0, samps_per_chan=1000)

    ai_task.start()

    event_observer.wait_for_events()
    with pytest.raises(TimeoutError):
        event_observer.wait_for_events(timeout=100e-3)
    assert len(event_observer.events) == 1
    assert all(e.status == 0 for e in event_observer.events)


@pytest.mark.library_only
def test___every_n_samples_event_registered___run_finite_acquisition___callback_invoked_n_times_with_type_and_num_samples(
    ai_task: nidaqmx.Task,
) -> None:
    event_observer = EveryNSamplesEventObserver()
    ai_task.register_every_n_samples_acquired_into_buffer_event(
        100, event_observer.handle_every_n_samples_event
    )
    ai_task.timing.cfg_samp_clk_timing(rate=10000.0, samps_per_chan=1000)

    ai_task.start()

    event_observer.wait_for_events(10)
    with pytest.raises(TimeoutError):
        event_observer.wait_for_events(timeout=100e-3)
    assert len(event_observer.events) == 10
    assert all(
        e.event_type == EveryNSamplesEventType.ACQUIRED_INTO_BUFFER.value
        for e in event_observer.events
    )
    assert all(e.number_of_samples == 100 for e in event_observer.events)


@pytest.mark.library_only
def test___signal_event_registered___run_finite_acquisition___callback_invoked_n_times_with_type(
    ai_task_with_real_device: nidaqmx.Task,
) -> None:
    ai_task = ai_task_with_real_device
    event_observer = SignalEventObserver()
    ai_task.register_signal_event(Signal.SAMPLE_COMPLETE, event_observer.handle_signal_event)
    ai_task.timing.cfg_samp_clk_timing(rate=10.0, samps_per_chan=10)

    ai_task.start()

    event_observer.wait_for_events(10)
    with pytest.raises(TimeoutError):
        event_observer.wait_for_events(timeout=100e-3)
    assert len(event_observer.events) == 10
    assert all(e.signal_type == Signal.SAMPLE_COMPLETE.value for e in event_observer.events)


@pytest.mark.library_only
def test___done_event_unregistered___run_finite_acquisition___callback_not_invoked(
    ai_task: nidaqmx.Task,
) -> None:
    event_observer = DoneEventObserver()
    ai_task.register_done_event(event_observer.handle_done_event)
    ai_task.register_done_event(None)
    ai_task.timing.cfg_samp_clk_timing(rate=10000.0, samps_per_chan=1000)

    ai_task.start()
    ai_task.wait_until_done()

    with pytest.raises(TimeoutError):
        event_observer.wait_for_events(timeout=100e-3)
    assert len(event_observer.events) == 0


@pytest.mark.library_only
def test___every_n_samples_event_unregistered___run_finite_acquisition___callback_not_invoked(
    ai_task: nidaqmx.Task,
) -> None:
    event_observer = EveryNSamplesEventObserver()
    ai_task.register_every_n_samples_acquired_into_buffer_event(
        100, event_observer.handle_every_n_samples_event
    )
    ai_task.register_every_n_samples_acquired_into_buffer_event(100, None)
    ai_task.timing.cfg_samp_clk_timing(rate=10000.0, samps_per_chan=1000)

    ai_task.start()
    ai_task.wait_until_done()

    with pytest.raises(TimeoutError):
        event_observer.wait_for_events(timeout=100e-3)
    assert len(event_observer.events) == 0


@pytest.mark.library_only
def test___signal_event_unregistered___run_finite_acquisition___callback_not_invoked(
    ai_task_with_real_device: nidaqmx.Task,
) -> None:
    ai_task = ai_task_with_real_device
    event_observer = SignalEventObserver()
    ai_task.register_signal_event(Signal.SAMPLE_COMPLETE, event_observer.handle_signal_event)
    ai_task.register_signal_event(Signal.SAMPLE_COMPLETE, None)
    ai_task.timing.cfg_samp_clk_timing(rate=10.0, samps_per_chan=10)

    ai_task.start()
    ai_task.wait_until_done()

    with pytest.raises(TimeoutError):
        event_observer.wait_for_events(timeout=100e-3)
    assert len(event_observer.events) == 0


@pytest.mark.library_only
def test___done_and_every_n_samples_events_registered___run_finite_acquisition___callbacks_invoked(
    ai_task: nidaqmx.Task,
) -> None:
    done_event_observer = DoneEventObserver()
    every_n_samples_event_observer = EveryNSamplesEventObserver()
    ai_task.register_done_event(done_event_observer.handle_done_event)
    ai_task.register_every_n_samples_acquired_into_buffer_event(
        100, every_n_samples_event_observer.handle_every_n_samples_event
    )
    ai_task.timing.cfg_samp_clk_timing(rate=10000.0, samps_per_chan=1000)

    ai_task.start()

    done_event_observer.wait_for_events()
    every_n_samples_event_observer.wait_for_events(10)
    assert len(done_event_observer.events) == 1
    assert len(every_n_samples_event_observer.events) == 10


@pytest.mark.library_only
def test___done_and_every_n_samples_events_registered___run_multiple_finite_acquisitions___callbacks_invoked(
    ai_task: nidaqmx.Task,
) -> None:
    done_event_observer = DoneEventObserver()
    every_n_samples_event_observer = EveryNSamplesEventObserver()
    ai_task.register_done_event(done_event_observer.handle_done_event)
    ai_task.register_every_n_samples_acquired_into_buffer_event(
        100, every_n_samples_event_observer.handle_every_n_samples_event
    )
    ai_task.timing.cfg_samp_clk_timing(rate=10000.0, samps_per_chan=1000)

    for _ in range(3):
        ai_task.start()
        done_event_observer.wait_for_events()
        every_n_samples_event_observer.wait_for_events(10)
        ai_task.stop()

    assert len(done_event_observer.events) == 3
    assert len(every_n_samples_event_observer.events) == 30


@pytest.mark.library_only
def test___done_event_registered___register_done_event___already_registered_error_raised(
    ai_task: nidaqmx.Task,
) -> None:
    event_observer = DoneEventObserver()
    ai_task.register_done_event(event_observer.handle_done_event)
    ai_task.timing.cfg_samp_clk_timing(rate=10000.0, samps_per_chan=1000)

    with pytest.raises(nidaqmx.DaqError) as exc_info:
        ai_task.register_done_event(event_observer.handle_done_event)

    assert exc_info.value.error_code == DAQmxErrors.DONE_EVENT_ALREADY_REGISTERED


@pytest.mark.library_only
def test___every_n_samples_acquired_into_buffer_event_registered___register_every_n_samples_acquired_into_buffer_event___already_registered_error_raised(
    ai_task: nidaqmx.Task,
) -> None:
    event_observer = EveryNSamplesEventObserver()
    ai_task.register_every_n_samples_acquired_into_buffer_event(
        100, event_observer.handle_every_n_samples_event
    )
    ai_task.timing.cfg_samp_clk_timing(rate=10000.0, samps_per_chan=1000)

    with pytest.raises(nidaqmx.DaqError) as exc_info:
        ai_task.register_every_n_samples_acquired_into_buffer_event(
            100, event_observer.handle_every_n_samples_event
        )

    assert (
        exc_info.value.error_code
        == DAQmxErrors.EVERY_N_SAMPS_ACQ_INTO_BUFFER_EVENT_ALREADY_REGISTERED
    )


@pytest.mark.library_only
def test___every_n_samples_transferred_from_buffer_event_registered___register_every_n_samples_transferred_from_buffer_event___already_registered_error_raised(
    ao_task: nidaqmx.Task,
) -> None:
    event_observer = EveryNSamplesEventObserver()
    ao_task.register_every_n_samples_transferred_from_buffer_event(
        100, event_observer.handle_every_n_samples_event
    )
    ao_task.timing.cfg_samp_clk_timing(rate=10000.0, samps_per_chan=1000)

    with pytest.raises(nidaqmx.DaqError) as exc_info:
        ao_task.register_every_n_samples_transferred_from_buffer_event(
            100, event_observer.handle_every_n_samples_event
        )

    assert (
        exc_info.value.error_code
        == DAQmxErrors.EVERY_N_SAMPS_TRANSFERRED_FROM_BUFFER_EVENT_ALREADY_REGISTERED
    )


@pytest.mark.library_only
def test___signal_event_registered___register_signal_event___already_registered_error_raised(
    ai_task: nidaqmx.Task,
) -> None:
    event_observer = SignalEventObserver()
    ai_task.register_signal_event(Signal.SAMPLE_COMPLETE, event_observer.handle_signal_event)
    ai_task.timing.cfg_samp_clk_timing(rate=10000.0, samps_per_chan=1000)

    with pytest.raises(nidaqmx.DaqError) as exc_info:
        ai_task.register_signal_event(Signal.SAMPLE_COMPLETE, event_observer.handle_signal_event)

    assert exc_info.value.error_code == DAQmxErrors.SIGNAL_EVENT_ALREADY_REGISTERED


@pytest.mark.library_only
def test___task___register_unregister_done_event___callback_not_invoked(
    ai_task: nidaqmx.Task,
) -> None:
    event_observer = DoneEventObserver()

    for _ in range(10):
        ai_task.register_done_event(event_observer.handle_done_event)
        ai_task.register_done_event(None)

    assert len(event_observer.events) == 0


@pytest.mark.library_only
def test___task___register_unregister_every_n_samples_acquired_into_buffer_event___callback_not_invoked(
    ai_task: nidaqmx.Task,
) -> None:
    event_observer = EveryNSamplesEventObserver()

    for _ in range(10):
        ai_task.register_every_n_samples_acquired_into_buffer_event(
            100, event_observer.handle_every_n_samples_event
        )
        ai_task.register_every_n_samples_acquired_into_buffer_event(100, None)

    assert len(event_observer.events) == 0


@pytest.mark.library_only
def test___task___register_unregister_every_n_samples_transferred_from_buffer_event___callback_not_invoked(
    ao_task: nidaqmx.Task,
) -> None:
    event_observer = EveryNSamplesEventObserver()

    for _ in range(10):
        ao_task.register_every_n_samples_transferred_from_buffer_event(
            100, event_observer.handle_every_n_samples_event
        )
        ao_task.register_every_n_samples_transferred_from_buffer_event(100, None)

    assert len(event_observer.events) == 0


@pytest.mark.library_only
def test___task___register_unregister_signal_event___callback_not_invoked(
    ai_task: nidaqmx.Task,
) -> None:
    event_observer = SignalEventObserver()

    for _ in range(10):
        ai_task.register_signal_event(Signal.SAMPLE_COMPLETE, event_observer.handle_signal_event)
        ai_task.register_signal_event(Signal.SAMPLE_COMPLETE, None)

    assert len(event_observer.events) == 0
