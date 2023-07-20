export class Store<T> {
    state: T;
    listeners: ((state: T) => void)[];
  
    constructor(initialState: T, listeners?: ((state: T) => void)[]) {
      this.state = initialState;
      this.listeners = listeners ?? [];
    }
  
    set(newState: T) {
      this.state = newState;
      this.notifyListeners();
    }
  
    update(updater: (prevState: T) => T) {
      this.state = updater(this.state);
      this.notifyListeners();
    }
  
    subscribe(listener: (state: T) => void) {
      this.listeners.push(listener);
    }
  
    notifyListeners() {
      for (let listener of this.listeners) {
        listener(this.state);
      }
    }
  }