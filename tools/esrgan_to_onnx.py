"""Read Real-ESRGAN realesr-general-x4v3.pth without torch and write an ONNX model (SRVGGNetCompact)."""
import zipfile, pickle, numpy as np, collections, sys
import onnx
from onnx import helper, TensorProto, numpy_helper

z = zipfile.ZipFile(sys.argv[1])
pre = z.namelist()[0].split('/')[0]

class Storage:
    def __init__(self, key, dtype): self.key, self.dtype = key, dtype

def rebuild(storage, offset, size, stride, *a):
    raw = np.frombuffer(z.read(f'{pre}/data/{storage.key}'), dtype=storage.dtype)
    n = int(np.prod(size)) if size else 1
    return raw[offset:offset + n].reshape(size).copy()

class U(pickle.Unpickler):
    def find_class(self, mod, name):
        if name == '_rebuild_tensor_v2': return rebuild
        if name == 'FloatStorage': return np.float32
        if name == 'HalfStorage': return np.float16
        if name == 'OrderedDict': return collections.OrderedDict
        if mod == 'torch' and name.endswith('Storage'): return np.float32
        return super().find_class(mod, name)
    def persistent_load(self, pid):
        _, dt, key, loc, n = pid
        return Storage(key, dt if isinstance(dt, type) else np.float32)

sd = U(z.open(f'{pre}/data.pkl')).load()
if 'params' in sd: sd = sd['params']
keys = list(sd.keys())
print(len(keys), keys[:6], keys[-4:])

nodes, inits = [], []
def init(name, arr):
    inits.append(numpy_helper.from_array(arr.astype(np.float32), name)); return name

x = 'input'
cur = x
idx = sorted({int(k.split('.')[1]) for k in keys})
for i in idx:
    w = sd.get(f'body.{i}.weight'); b = sd.get(f'body.{i}.bias')
    if w is None: continue
    if w.ndim == 4:
        o = f'c{i}'
        nodes.append(helper.make_node('Conv', [cur, init(f'w{i}', w), init(f'b{i}', b)], [o], pads=[1, 1, 1, 1], kernel_shape=[3, 3]))
    else:  # PReLU
        o = f'p{i}'
        nodes.append(helper.make_node('PRelu', [cur, init(f'a{i}', w.reshape(-1, 1, 1))], [o]))
    cur = o
nodes.append(helper.make_node('DepthToSpace', [cur], ['ps'], blocksize=4, mode='CRD'))
nodes.append(helper.make_node('Resize', [x, '', init('scales', np.array([1, 1, 4, 4], np.float32))], ['up'], mode='nearest'))
nodes.append(helper.make_node('Add', ['ps', 'up'], ['output']))
g = helper.make_graph(nodes, 'realesr_general_x4v3', [helper.make_tensor_value_info('input', TensorProto.FLOAT, [1, 3, 'h', 'w'])],
                      [helper.make_tensor_value_info('output', TensorProto.FLOAT, [1, 3, 'H', 'W'])], inits)
m = helper.make_model(g, opset_imports=[helper.make_opsetid('', 13)]); m.ir_version = 8
onnx.checker.check_model(m)
onnx.save(m, sys.argv[2])
print('saved')
