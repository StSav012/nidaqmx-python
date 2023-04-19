from nidaqmx.task import Task

from nidaqmx import utils


class _TaskAlternateConstructor(Task):
    """
    Provide an alternate constructor for the Task object.

    Since we want the user to create a Task simply by instantiating a
    Task object, thus, the Task object's constructor has a DAQmx Create
    Task call.

    Instantiating a Task object from a task handle - as required by
    PersistedTask.load(), requires that we either change the original
    constructor's prototype and add a parameter, or that we create this
    derived class to 'overload' the constructor.
    """

    def __init__(self, task_handle,*, grpc_options=None, interpreter=None):
        """
        Args:
            task_handle: Specifies the task handle from which to create a
                Task object.
            grpc_options: Specifies the gRPC session options.
        """
        self._handle = task_handle
        self._interpreter = utils._select_interpreter(grpc_options, interpreter)

        self._initialize(self._handle, self._interpreter)

        # Use meta-programming to change the type of this object to Task,
        # so the user isn't confused when doing introspection. Not pretty,
        # but works well.
        self.__class__ = Task
