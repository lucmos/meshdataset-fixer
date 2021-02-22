import subprocess
from itertools import chain
from pathlib import Path
from typing import List, Optional, Any, Sequence, Callable, Tuple
import meshio
import shutil
import tempfile
import uuid
from src.utils import get_env
from gladia.plotter.shape import plot_mesh, plot_meshes

from loguru import logger


def direct_copy(filepath: Path, target_path: Path):
    if filepath and filepath.is_file():
        logger.warning(f"Direct copy: {filepath} -> {target_path}")
        shutil.copy(filepath, target_path)


class ManifoldFix:
    def __init__(self, resolution: int = 5_000, executable: Optional[str] = None):
        self.resolution = resolution
        self.executable = executable
        if executable is None:
            self.executable = get_env("manifold", default="manifold")

    def __call__(
        self, source_path: Path, target_path: Path
    ) -> Tuple[Path, Sequence[Path]]:
        try:

            cmd = " ".join(
                [
                    self.executable,
                    str(source_path),
                    str(target_path),
                    f"{self.resolution}",
                ]
            )
            logger.info(cmd)
            subprocess.check_call(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL
                # stderr=subprocess.DEVNULL,
            )
            return target_path, []
        except Exception as e:
            logger.error(f"Error manifold: {source_path} -> {target_path}")
            raise e

    def __repr__(self) -> str:
        return f"ManifoldFix(resolution={self.resolution})"


class ManifoldSimplify:
    def __init__(
        self,
        manifold_check: bool = True,
        face_num: int = 5_000,
        max_cost: int = 1e-6,
        max_ratio: int = 0.40,
        executable: Optional[str] = None,
    ):
        self.manifold_check = manifold_check
        self.max_cost = max_cost
        self.face_num = face_num
        self.max_ratio = max_ratio

        self.executable = executable
        if executable is None:
            self.executable = get_env("simplify", default="simplify")

    def __call__(
        self, source_path: Path, target_path: Path
    ) -> Tuple[Path, Sequence[Path]]:
        try:
            # meshio.read('data-fixed/44.obj').points.shape, plot_mesh('data-fixed/44.obj', autoshow=True)
            cmd = " ".join(
                [
                    self.executable,
                    "-i",
                    str(source_path),
                    "-o",
                    str(target_path),
                    f"-m" if self.manifold_check else "",
                    f"-f {self.face_num}",
                    f"-c {self.max_cost}",
                    f"-r {self.max_ratio}",
                ]
            )
            logger.info(cmd)
            subprocess.check_call(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                # stderr=subprocess.DEVNULL,
            )
            return target_path, []
        except Exception as e:
            logger.error(f"Error simplify: {source_path} -> {target_path}")
            raise e

    def __repr__(self) -> str:
        return (
            f"ManifoldSimplify("
            f"manifold_check={self.manifold_check}, "
            f"face_num={self.face_num}, "
            f"max_cost={self.max_cost}, "
            f"max_ratio={self.max_ratio})"
        )


class ManifoldConvert:
    def __init__(self, target_format: str = ".obj"):
        if target_format and target_format[0] != ".":
            raise ValueError(
                f"The target format {target_format} is not a suffix! "
                f"It should start with a dot."
            )
        self.target_format = target_format

    def convert_shape_format(
        self, source_path: Path, target_path: Path
    ) -> Tuple[Path, Sequence[Path]]:
        target_path = target_path.with_suffix(self.target_format)
        meshio.write(
            str(target_path),
            meshio.read(source_path),
            file_format=self.target_format[1:],
        )
        logger.info(f"{source_path} -> {target_path}")
        return target_path, []

    def fix_broken_off(self, source_path: Path) -> Tuple[Path, Sequence[Path]]:
        text = source_path.read_text()
        if text[3] != "\n":
            text = text[:3] + "\n" + text[3:]
            temp_path = Path(tempfile.gettempdir()) / f"{str(uuid.uuid4())}.off"
            temp_path.write_text(text)
            return temp_path, [temp_path]
        return source_path, []

    def __call__(
        self, source_path: Path, target_path: Path
    ) -> Tuple[Path, Sequence[Path]]:
        if source_path.suffix != ".off":
            return self.convert_shape_format(source_path, target_path)

        source_path, temp_files = self.fix_broken_off(source_path)
        out_path, temp_files_2 = self.convert_shape_format(source_path, target_path)

        return out_path, list(chain.from_iterable([temp_files, temp_files_2]))

    def __repr__(self) -> str:
        return "ManifoldToObj()"
