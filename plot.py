# Copyright(C) 2018 ga-developers
#
# Repository: https://github.com/ga-developers/ga-benchmark.git
#
# This file is part of the GA-Benchmark project.
#
# GA-Benchmark is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GA-Benchmark is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GA-Benchmark. If not, see <https://www.gnu.org/licenses/>.

import argparse, os, json, sys
import matplotlib as mpl, matplotlib.pyplot as plt
import numpy as np
from typing import Tuple
from mpl_toolkits.mplot3d import Axes3D


MODELS = [None, 'ConformalModel', 'EuclideanModel', 'HomogeneousModel', 'MinkowskiModel']


def _context_to_key(context: dict) -> str:
    """Convert the context structure into a key for grouping benchmarks evaluated under the same conditions.
    :param context: the context of the benchmark.
    :return: a string describing the context.
    """
    return 'BuildType-%s, NumCPUs-%d, MHzPerCPU-%d, CPUScaling-%s, LoadAvg-%s' % (
        context['library_build_type'],
        context['num_cpus'],
        context['mhz_per_cpu'],
        str(context['cpu_scaling_enabled']),
        str(context['load_avg'])
    )


def _parse_benchmark_name(name: str) -> Tuple[str, str, str, str, int, dict]:
    """Parse benchmark name to a set of values.
    :param name: the name of the benchmark.
    :return: (library, group, operation, model, d, args), where 'library' identifies the library or library generator, 'group' and 'operation' define the procedure, 'model' and 'd' specify an algebra of R^d, and 'args' defines the specialization of the procedure to some case.
    """
    params = name.split('/')

    _, group, operation = params[0].split('_')

    library, model, d, args = None, None, None, dict()
    for pair in params[1:]:
        key, value = pair.split('=')
        if key == 'Library':
            library = value
        elif key == 'Model':
            model = MODELS[int(value, base=16)]
        elif key == 'D':
            d = int(value)
        else:
            try: args[key] = int(value)
            except ValueError: args[key] = value

    return library, group, operation, model, d, args


def _read_data(folder: str, verbose: bool) -> Tuple[dict, list]:
    """Read benchmark results from JSON files found in the given folder and returns tabulated data.
    :param folder: the path to the folder containing the JSON files generated by the ga-benchmark tool.
    :param verbose: indicates whether the processing messages should be displayed.
    :return: (data, all_libraries), where data is a dictionary with tabulated results and all_libraries is a list including the name of all libraries and library generators.
    """
    def message(msg, *argv):
        if verbose: print(msg % argv, end='')

    data = dict()
    all_libraries = set()
    success, fail = 0, 0
    message('Reading JSON files in "%s"\n', folder)
    for filename in sorted(os.listdir(folder)):
        filepath = os.path.join(folder, filename)
        if os.path.isfile(filepath) and filename.endswith('.json'):
            message('  Parsing "%s"... ', filename)
            with open(filepath) as f:
                try:
                    raw_data = json.load(f)
                except:
                    fail += 1  # Errors while trying to load JSON data are the only accepted ones.
                    message('error\n')
                    continue
            constext_key = _context_to_key(raw_data.get('context'))
            for bm in raw_data.get('benchmarks', list()):
                library, group, operation, model, d, args = _parse_benchmark_name(bm['name'])
                cpu_time = bm['cpu_time']
                real_time = bm['real_time']
                metrics = data.setdefault(constext_key, dict())
                for metric, value in [('cpu_time', cpu_time), ('real_time', real_time)]:
                    models = metrics.setdefault(metric, dict())
                    dimensions = models.setdefault(model, dict())
                    groups = dimensions.setdefault(d, dict())
                    operations = groups.setdefault(group, dict())
                    libraries = operations.setdefault(operation, dict())
                    if group == 'Product':
                        values = libraries.setdefault(library, dict())
                        values[(args['LeftGrade'], args['RightGrade'])] = value
                    elif group == 'Algorithm':
                        values = libraries.setdefault(library, value)
                    else:
                        raise NotImplementedError('The "%s" group is not supported yet.' % group)
                all_libraries.add(library)
            success += 1
            message('done\n')
    message('  Success: %d, Fail: %d\n\n', success, fail)
    return data, list(sorted(all_libraries))


def _get_axes_bounds_for_products(operations: dict) -> Tuple[int, int, int, int, int, int]:
    """Return the min and max values assumed in each dimension of the 3D plot.
    :param operations: a sub-dictionary returned by the _read_data(...) function including only the results for the operations in the 'Product' group.
    :return: (x_min, x_max, y_min, y_max, z_min, z_max) define the limits of the 3D plot.
    """
    x_min, y_min, z_min = sys.maxsize, sys.maxsize, 0
    x_max, y_max, z_max = -sys.maxsize, -sys.maxsize, -sys.maxsize
    for libraries in operations.values():
        for values in libraries.values():
            for xy, value in values.items():
                x_min, y_min = min(x_min, xy[0]), min(y_min, xy[1])
                x_max, y_max, z_max = max(x_max, xy[0]), max(y_max, xy[1]), max(z_max, value)
    return x_min, x_max, y_min, y_max, z_min, z_max


def _plot_data(data: dict, all_libraries: list, folder: str, verbose: bool) -> None:
    """Produce PDF files showing charts and tables with the results.
    :param data: a dictionary returned by the _read_data(...) function.
    :param all_libraries: a list including the name of all libraries and library generators.
    :param folder: the path to the folder where the files will be written.
    :param verbose: indicates whether the processing messages should be displayed.
    """
    def message(msg, *argv):
        if verbose: print(msg % argv, end='')

    cmap = plt.get_cmap('Paired')

    message('Writing charts and tables to the output folder "%s"\n', folder)
    for context_key, metrics in data.items():
        for metric, models in metrics.items():
            for model, dimensions in models.items():
                for d, groups in dimensions.items():
                    for group, operations in groups.items():
                        if group == 'Algorithm':
                            for operation, libraries in operations.items():
                                relative_path = os.path.join(context_key, metric, model, str(d), group, operation)
                                message('  Plotting results to "%s"... ', os.path.join('OUTPUT_FOLDER', relative_path))
                                os.makedirs(os.path.join(folder, relative_path), exist_ok=True)
                                libraries, values = zip(*sorted(libraries.items()))

                                fig = plt.figure('%s %dD - %s, %s - %s' % (model, d, group, operation, metric))
                                ax = fig.add_subplot(111)
                                ax.set_xlabel('Libraries')
                                ax.set_ylabel('ms')
                                for tick in ax.xaxis.get_major_ticks():
                                    tick.label.set_rotation('vertical')
                                plt.bar(np.arange(1, len(libraries) + 1), values, tick_label=libraries, color=[mpl.colors.rgb2hex(cmap(all_libraries.index(library) / (len(all_libraries) - 1))) for library in libraries])
                                fig.tight_layout()
                                fig.savefig(os.path.join(folder, relative_path, 'Result.pdf'))
                                # plt.show()
                                plt.close(fig)
                                message('done\n')
                        elif group == 'Product':
                            x_min, x_max, y_min, y_max, z_min, z_max = _get_axes_bounds_for_products(operations)
                            X, Y = np.meshgrid(np.arange(x_min, x_max + 1), np.arange(y_min, y_max + 1))
                            X_, Y_ = X.ravel() - 0.5, Y.ravel() - 0.5
                            for operation, libraries in operations.items():
                                relative_path = os.path.join(context_key, metric, model, str(d), group, operation)
                                message('  Plotting results to "%s"... ', os.path.join('OUTPUT_FOLDER', relative_path))
                                os.makedirs(os.path.join(folder, relative_path), exist_ok=True)
                                best_library = np.full(X.shape, '', np.object)
                                best_color_ind = np.full(X.shape, -1, np.float32)
                                best_Z = np.full(X.shape, float('inf'), np.float32)
                                for library, values in libraries.items():
                                    color_ind = all_libraries.index(library) / (len(all_libraries) - 1)
                                    color = mpl.colors.rgb2hex(cmap(color_ind))

                                    Z = np.full(X.shape, float('inf'), np.float32)
                                    for xy, z in values.items():
                                        Z[xy[1] - y_min, xy[0] - x_min] = z

                                    replace = Z < best_Z
                                    best_library[replace] = library
                                    best_color_ind[replace] = color_ind
                                    best_Z[replace] = Z[replace]

                                    fig = plt.figure('%s %dD - %s, %s - %s - %s' % (model, d, group, operation, library, metric))
                                    ax = fig.add_subplot(111, projection='3d')
                                    ax.set_xlabel('LHS Grade')
                                    ax.set_xlim3d(x_min - 0.5, x_max + 0.5)
                                    ax.set_xticks(np.arange(x_min, x_max + 1))
                                    ax.set_ylabel('RHS Grade')
                                    ax.set_ylim3d(y_min - 0.5, y_max + 0.5)
                                    ax.set_yticks(np.arange(y_min, y_max + 1))
                                    ax.set_zlabel('ms')
                                    ax.set_zlim3d(z_min, z_max)
                                    ax.bar3d(X_, Y_, np.zeros_like(X_), 1, 1, Z.ravel(), color=color, edgecolor=(0, 0, 0), shade=True, antialiased=True)
                                    ax.legend([mpl.lines.Line2D([0],[0], linestyle="none", color=color, marker='o')], [library], numpoints=1)
                                    fig.tight_layout()
                                    fig.savefig(os.path.join(folder, relative_path, library + '.pdf'))
                                    # plt.show()
                                    plt.close(fig)

                                fig = plt.figure('%s %dD - %s, %s - %s' % (model, d, group, operation, metric))
                                ax = fig.add_subplot(111)
                                ax.set_xlabel('LHS Grade')
                                ax.set_xticks(np.arange(x_min, x_max + 1))
                                ax.set_ylabel('RHS Grade')
                                ax.set_yticks(np.arange(y_min, y_max + 1))
                                ax.imshow(best_color_ind, interpolation='none', origin='lower', cmap=cmap, vmin=0, vmax=1)
                                for x, y in zip(X.flatten(), Y.flatten()):
                                    ax.text(x, y, '%s\n%1.5f ms' % (best_library[y-y_min, x-x_min], best_Z[y-y_min, x-x_min]), va='center', ha='center', fontsize=6)
                                fig.tight_layout()
                                fig.savefig(os.path.join(folder, relative_path, 'Result.pdf'))
                                # plt.show()
                                plt.close(fig)
                                message('done\n')
                        else:
                            raise NotImplementedError('The "%s" group is not supported yet.' % group)


def main(argsv=None):
    """Main function.
    """
    if argsv is None: argsv = sys.argv[1:]

    ap = argparse.ArgumentParser('python3 -m plot [-i INPUT_FOLDER] [-o OUTPUT_FOLDER] [-s]')
    ap.add_argument('-i', '--input', metavar='INPUT_FOLDER', required=False, default='.', help='Folder containing the JSON files generated by the ga-benchmark tool (default: current folder).')
    ap.add_argument('-o', '--output', metavar='OUTPUT_FOLDER', required=False, default='./results', help='Folder to which the charts and tables will be exported (default: [current folder]/results).')
    ap.add_argument('-s', '--silent', required=False, default=False, action='store_true', help='Defines whether the processing messages should be skipped. (default: False).')

    args = vars(ap.parse_args(argsv))

    data, all_libraries = _read_data(folder=args['input'], verbose=not args['silent'])
    _plot_data(data=data, all_libraries=all_libraries, folder=args['output'], verbose=not args['silent'])



if __name__ == "__main__":
    main()