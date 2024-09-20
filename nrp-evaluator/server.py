import kubernetes

import logging

from openff.evaluator.backends.dask import BaseDaskBackend, QueueWorkerResources, _Multiprocessor
from openff.evaluator.server import EvaluatorServer
import distributed

logger = logging.getLogger(__name__)



class DaskKubernetesCluster(BaseDaskBackend):
    def __init__(
        self,
        image: str,
        number_of_workers: int =1,
        resources_per_worker=QueueWorkerResources(),
        name: str = "openff-evaluator-dask-cluster",
    ):
        super().__init__(number_of_workers, resources_per_worker)

        assert isinstance(resources_per_worker, QueueWorkerResources)

        if resources_per_worker.number_of_gpus > 0:
            if resources_per_worker.number_of_gpus > 1:
                raise ValueError("Only one GPU per worker is currently supported.")

        self._image = image
        self._name = name

    def start(self):
        from dask_kubernetes.operator import KubeCluster

        self._cluster = KubeCluster(
            name=self._name,
            image=self._image,
        )
        self._cluster.scale(self._number_of_workers)
        super().start()

    @staticmethod
    def _wrapped_function(function, *args, **kwargs):
        available_resources = kwargs["available_resources"]
        gpu_assignments = kwargs.pop("gpu_assignments")

        if available_resources.number_of_gpus > 0:
            worker_id = distributed.get_worker().id

            available_resources._gpu_device_indices = (
                "0" if worker_id not in gpu_assignments else gpu_assignments[worker_id]
            )

            logger.info(
                f"Launching a job with access to GPUs "
                f"{available_resources._gpu_device_indices}"
            )


        return_value = _Multiprocessor.run(function, *args, **kwargs)
        return return_value

    def submit_task(self, function, *args, **kwargs):
        key = kwargs.pop("key", None)

        return self._client.submit(
            DaskKubernetesCluster._wrapped_function,
            function,
            *args,
            **kwargs,
            key=key,
            available_resources=self._resources_per_worker,
            gpu_assignments={},
        )


with DaskKubernetesCluster() as calculation_backend:

    evaluator_server = EvaluatorServer(calculation_backend)
    evaluator_server.start()
