let registry: { [key: string]: Function | null } = {};

export const pub = (key: string, ...args: any) => {
    console.log('pubbing')
    console.log(key)
//   if (!registry[key]) return;
    const fn = registry[key]
    if(!fn) throw new Error('published to an unawaited key')
  fn.apply(null, args);
  registry[key] = null;

};

export const sub = (key: string, fn: (...args: any) => void) => {
    console.log('subbing')
    console.log(key)
  if (registry[key]) throw new Error("Only one subscription allowed");
  registry[key] = fn;
};

const PubSub = { pub, sub };

export default PubSub;