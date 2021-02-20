from multiprocessing import Pool
from pathlib import Path
from typing import Sequence, Callable, Tuple
import meshio
from gladia.plotter.shape import plot_mesh, plot_meshes
import dotenv
import tempfile
import uuid

from loguru import logger

from src.transforms import direct_copy


class DatasetConverter:
    def __init__(
        self,
        transforms: Sequence[Callable[[Path, Path], Tuple[Path, Sequence[Path]]]],
        fallback: Callable = direct_copy,
        source: str = "data-raw",
        target: str = "data-fixed",
    ):
        dotenv.load_dotenv(override=True)
        self.transforms = transforms
        self.fallback = fallback

        self.tmp_dir = Path(tempfile.gettempdir())

        self.source: Path = Path(source)
        self.target: Path = Path(target)

        self.shapes = sorted(self.source.rglob("*"))
        # import random
        # random.shuffle(self.shapes)

    def ensure_dir(self, target_path: Path) -> None:
        if target_path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)

    def get_temp_path(self) -> Path:
        return self.tmp_dir / f"{str(uuid.uuid4())}.obj"

    def get_target_path(self, source_path: Path) -> Path:
        target_path = self.target / source_path.relative_to(self.source)
        self.ensure_dir(target_path)
        return target_path

    def convert_shape(self, shape_path: Path):
        target_path = self.get_target_path(shape_path)
        all_temp_paths = []
        try:
            outpaths = [self.get_temp_path() for _ in range(len(self.transforms) - 1)]
            outpaths.append(target_path.with_suffix(".obj"))
            for transform, outpath in zip(self.transforms, outpaths):
                outpath, temp_paths = transform(shape_path, outpath)
                shape_path = outpath
                all_temp_paths.extend(temp_paths)

        except meshio._exceptions.ReadError:
            logger.warning(f"Direct copy: {shape_path}")
            self.fallback(shape_path, target_path)

        finally:
            for x in all_temp_paths:
                x.unlink()

    def transform_dataset(self, processes: int = 8, parallel: bool = False) -> None:
        if parallel:
            with Pool(processes=processes) as pool:
                # print "[0, 1, 4,..., 81]"
                # print same numbers in arbitrary order
                for x in pool.imap_unordered(
                    self.convert_shape, self.shapes, chunksize=1000
                ):
                    pass
        else:
            for x in self.shapes:
                self.convert_shape(x)
