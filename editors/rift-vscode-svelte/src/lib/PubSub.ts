export module PubSub {
    var registry: { [key: string]: Function | null } = {};
    export var pub = function (key: string, ...args: any) {
        if (!registry[key]) return;

        registry[key]?.apply(null, args);
        registry[key] = null;
    };
    export var sub = function (key: string, fn: Function) {
        if (registry[key]) throw Error("Only one subscription allowed");
        registry[key] = fn;
    };
}

