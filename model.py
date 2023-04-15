import torch
import torch.nn as nn
from torch.nn import functional as F

#hyperparameters
batch_size = 32
block_size = 8
max_iters = 3000
eval_interval = 300
learning_rate = 1e-2
device = 'cuda' if torch.cuda.is_available() else 'cpu'
eval_iters = 200

torch.manual_seed(1337)

with open('train.txt', 'r', encoding='utf-8') as f:
    text = f.read()
    
chars = sorted(list(set(text)))
vocab_size = len(chars)
stoi = { ch:i for i,ch in enumerate(chars) }
itos = {i:ch for i,ch in enumerate(chars)}
encode = lambda s: [stoi[c] for c in s]
decode = lambda l: ''.join([itos[i] for i in l])
data = torch.tensor(encode(text),dtype=torch.long)
n = int(.9*len(data))
train_data = data[:n]
test_data = data[n:]

print(data.shape)

def get_batch(split):
    data = train_data if split == 'train' else test_data
    ix = torch.randint(len(data) - block_size, (batch_size,))
    x = torch.stack([data[i:i+block_size] for i in ix])
    y = torch.stack([data[i+1:i+block_size+1] for i in ix])
    return x,y

class BigramLanguageModel(nn.Module):
  
  def __init__(self, vocab_size):
    super().__init__()
    self.token_embedding_table = nn.Embedding(vocab_size,vocab_size)

  def forward(self, idx, targets=None):
    logits = self.token_embedding_table(idx)
    B,T,C = logits.shape
    logits = logits.view(B*T,C)
    
    loss = None
    if targets is not None:
      targets = targets.view(B*T)
      loss = F.cross_entropy(logits,targets)

    logits = logits.view(B,T,C)
    return logits, loss

  def generate(self,idx,max_new_tokens):
    for _ in range(max_new_tokens):
      logits, loss = self(idx)
      logits = logits[:,-1,:]
      probs = F.softmax(logits,dim=-1)
      idx_next = torch.multinomial(probs,num_samples=1).view(1,1)
      idx = torch.cat((idx,idx_next),dim=1)
    return idx

m = BigramLanguageModel(vocab_size)

optimizer = torch.optim.AdamW(m.parameters(), lr=1e-3)

for steps in range(1000):
  xb,yb = get_batch('train')

  logits, loss = m(xb,yb)
  optimizer.zero_grad(set_to_none=True)
  loss.backward()
  optimizer.step()
print(loss.item())
print(decode(m.generate(idx,max_new_tokens=100)[0].tolist()))