#!python3
#
from pathlib import Path
from typing import Optional

import meshio
from gladia.plotter.shape import plot_mesh

from src.converter import DatasetConverter
from src.transforms import ManifoldConvert, ManifoldFix, ManifoldSimplify
from src.utils import get_env
import typer
import json
from loguru import logger


def fix(
    resolution: int = typer.Option(
        5_000,
        help="the number of leaf nodes of octree. The face number increases linearly with the resolution.",
    ),
    simplify: bool = typer.Option(
        False, help="if True, tries to simplify the obtained manifold"
    ),
    manifold_check: bool = typer.Option(
        True, help="Turn on manifold check, we don't output model if check fails"
    ),
    face_num: int = typer.Option(
        5_000, help="Add termination condition when current_face_num <= face_num"
    ),
    max_cost: float = typer.Option(
        1e-6, help="Add termination condition when quadric error >= max_cost"
    ),
    max_ratio: float = typer.Option(
        0.40,
        help="Add termination condition when current_face_num / origin_face_num <= max_ratio",
    ),
    workers: int = typer.Option(8, help="if True parallelize the transformation"),
    parallel: bool = typer.Option(
        True, help="the number of workers to use if parallel is enabled"
    ),
    source: str = typer.Option("data-raw", help="the source folder"),
    target: str = typer.Option("data-fixed", help="the target folder"),
    manifold_exec: Optional[str] = typer.Option(
        None,
        help="the manifold executable. If None uses the one define in .env or in the path",
    ),
    simplify_exec: Optional[str] = typer.Option(
        None,
        help="the simplify executable. If None uses the one define in .env or in the path",
    ),
) -> None:
    """
    Fix a 3D dataset recursively to enforce watertight manifolds,
    it is copy-only. It does not change the source.

    It uses the Manifold tool: https://github.com/hjwdzh/Manifold
    """
    args = {x: y for x, y in locals().items() if not x.startswith("__")}

    logger.disable("src.transforms")

    with (Path(target) / "fixconfig.json").open(mode="w") as fp:
        json.dump(args, fp, indent=4, sort_keys=True)

    transforms = [
        ManifoldConvert(target_format=".obj"),
        ManifoldFix(resolution=resolution, executable=manifold_exec),
    ]

    if simplify:
        transforms.append(
            ManifoldSimplify(
                manifold_check=manifold_check,
                face_num=face_num,
                max_cost=max_cost,
                max_ratio=max_ratio,
                executable=simplify_exec,
            )
        )

    DatasetConverter(
        transforms=transforms,
        source=source,
        target=target,
    ).transform_dataset(processes=workers, parallel=parallel)


if __name__ == "__main__":
    typer.run(fix)
    #
    # a = sorted(list(Path("data-raw").rglob("*.off")))
    # b = sorted(list(Path("data-fixed").rglob("*.off")))
    # for x, y in zip(a, b):
    #     plot_mesh(x, autoshow=True)
    #     plot_mesh(y, autoshow=True)
    #     print(meshio.read(x).points.shape)

    import loguru
    import sys

    # # start 4 worker processes

    # for x in shapes:
    #     y = target / x.relative_to(source)
    #     y = y.with_suffix(".obj")
    #     try:
    #         print(x, y)
    #
    #     except:
    #         print(x, y)

    # evaluate "f(20)" asynchronously
    # res = pool.apply_async(f, (20,))  # runs in *only* one process
    # print(res.get(timeout=1))  # prints "400"

    # evaluate "os.getpid()" asynchronously
    # res = pool.apply_async(os.getpid, ())  # runs in *only* one process
    # print(res.get(timeout=1))  # prints the PID of that process

    # launching multiple evaluations asynchronously *may* use more processes
    # multiple_results = [pool.apply_async(os.getpid, ()) for i in range(4)]
    # print([res.get(timeout=1) for res in multiple_results])

    # make a single worker sleep for 10 secs
    # res = pool.apply_async(time.sleep, (10,))
    # try:
    #     print(res.get(timeout=1))
    # except TimeoutError:
    #     print("We lacked patience and got a multiprocessing.TimeoutError")
    #
    # print("For the moment, the pool remains available for more work")

    # exiting the 'with'-block has stopped the pool
    # print("Now the pool is closed and no longer available")
