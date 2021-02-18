import os
import subprocess
from multiprocessing import Pool
from pathlib import Path
from typing import List, Optional, Any
import meshio
from gladia.plotter.shape import plot_mesh, plot_meshes
import dotenv
import shutil
import tempfile
import uuid


dotenv.load_dotenv(override=True)
TMPDIR = Path(tempfile.gettempdir())

source: Path = Path("data-raw/")
target: Path = Path("data-fixed")

shapes = sorted(source.rglob("*"))


def get_env(env_name: str, default: Optional[Any] = None) -> str:
    """
    Read an environment variable.
    Raises errors if it is not defined or empty.

    :param env_name: the name of the environment variable
    :return: the value of the environment variable
    """
    if env_name not in os.environ:
        if default:
            return default
        raise KeyError(f"{env_name} not defined")
    env_value: str = os.environ[env_name]
    if not env_value:
        if default:
            return default
        raise KeyError(f"{env_name} has yet to be configured")
    return env_value


def direct_copy(filepath: Path, target_path: Path):
    if filepath.is_file():
        shutil.copy(filepath, target_path)


def manifold_call(shape_path: Path, target_path: Path):
    try:

        subprocess.check_call(
            [
                get_env("manifold", default="manifold"),
                str(shape_path),
                str(target_path),
            ],
            stdout=subprocess.DEVNULL,
            # stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"Error manifold: {shape_path} -> {target_path}")


def convert_and_fix(shape_path: Path, target_path: Path):
    temp_path = TMPDIR / f"{str(uuid.uuid4())}.obj"
    meshio.write(temp_path, meshio.read(shape_path), file_format="obj")
    target_path = target_path.with_suffix(".obj")
    shape_path = temp_path

    manifold_call(shape_path, target_path)

    temp_path.unlink()


def fix_off_and_fix_shapes(shape_path: Path, target_path: Path):
    text = shape_path.read_text()
    if text[3] != "\n":
        text = text[:3] + "\n" + text[3:]
        temp_path = TMPDIR / f"{str(uuid.uuid4())}.off"
        temp_path.write_text(text)
        shape_path = temp_path

        convert_and_fix(shape_path, target_path)

        temp_path.unlink()
    else:
        convert_and_fix(shape_path, target_path)


def fix_shapes(shape_path: Path, target_path: Path):
    if shape_path.is_file():
        if shape_path.suffix == ".off":
            fix_off_and_fix_shapes(shape_path, target_path)
        elif not shape_path.suffix == ".obj":
            convert_and_fix(shape_path, target_path)
        else:
            manifold_call(shape_path, target_path)


def convert_shape(shape_path: Path):
    target_path = target / shape_path.relative_to(source)
    if target_path.is_dir():
        target_path.mkdir(parents=True, exist_ok=True)
    else:
        target_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        fix_shapes(shape_path, target_path)
    except meshio._exceptions.ReadError:
        print(f"Direct copy: {shape_path}")
        direct_copy(shape_path, target_path)


if __name__ == "__main__":
    # # start 4 worker processes
    with Pool(processes=int(get_env("processes", default=8))) as pool:
        # print "[0, 1, 4,..., 81]"
        # print same numbers in arbitrary order
        for x in pool.imap_unordered(convert_shape, shapes, chunksize=1000):
            pass

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
