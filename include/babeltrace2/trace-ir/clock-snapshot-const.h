#ifndef BABELTRACE_TRACE_IR_CLOCK_SNAPSHOT_CONST_H
#define BABELTRACE_TRACE_IR_CLOCK_SNAPSHOT_CONST_H

/*
 * Copyright 2017-2018 Philippe Proulx <pproulx@efficios.com>
 * Copyright 2013, 2014 Jérémie Galarneau <jeremie.galarneau@efficios.com>
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 * The Common Trace Format (CTF) Specification is available at
 * http://www.efficios.com/ctf
 */

#include <stdint.h>

/* For bt_clock_class, bt_clock_snapshot */
#include <babeltrace2/types.h>

/* For __BT_FUNC_STATUS_* */
#define __BT_FUNC_STATUS_ENABLE
#include <babeltrace2/func-status.h>
#undef __BT_FUNC_STATUS_ENABLE

#ifdef __cplusplus
extern "C" {
#endif

extern const bt_clock_class *bt_clock_snapshot_borrow_clock_class_const(
		const bt_clock_snapshot *clock_snapshot);

extern uint64_t bt_clock_snapshot_get_value(
		const bt_clock_snapshot *clock_snapshot);

typedef enum bt_clock_snapshot_get_ns_from_origin_status {
	BT_CLOCK_SNAPSHOT_GET_NS_FROM_ORIGIN_STATUS_OK		= __BT_FUNC_STATUS_OK,
	BT_CLOCK_SNAPSHOT_GET_NS_FROM_ORIGIN_STATUS_OVERFLOW	= __BT_FUNC_STATUS_OVERFLOW,
} bt_clock_snapshot_get_ns_from_origin_status;

extern bt_clock_snapshot_get_ns_from_origin_status
bt_clock_snapshot_get_ns_from_origin(
		const bt_clock_snapshot *clock_snapshot,
		int64_t *ns_from_origin);

#ifdef __cplusplus
}
#endif

#include <babeltrace2/undef-func-status.h>

#endif /* BABELTRACE_TRACE_IR_CLOCK_SNAPSHOT_CONST_H */
