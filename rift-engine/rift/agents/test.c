int aa() {
  return 0;
}

void foo(int **x) {
  *x = 0;
}

int bb() {
  return 0;
}

/**
 * @brief The main function of the program. It initializes a pointer, calls the foo function to modify the pointer,
 * and then assigns a value to the pointed memory location.
 *
 * @return 0 indicating successful program execution.
 */
int main() {
  int *x;
  foo(&x);
  *x = 1;
  return 0;
}
