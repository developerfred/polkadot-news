import { MonoTypeOperatorFunction } from "rxjs";
/**
 * A RxJS pipeable operator which shares and replays the latest emitted value.
 * It's the equivalent of:
 *
 * ```ts
 * share<T>({
 *   connector: () => new ReplaySubject<T>(1),
 *   resetOnError: true,
 *   resetOnComplete: true,
 *   resetOnRefCountZero: true,
 * })
 * ```
 */
export declare const shareLatest: <T>() => MonoTypeOperatorFunction<T>;
