#include<stdlib.h>

int aa() {
  return 0;
}

void foo(int **x) {
  *x = NULL;
}

int bb() {
  return 0;
}

int main() {
  int *x;
  foo(&x);
  *x = 1;
  return 0;
}
