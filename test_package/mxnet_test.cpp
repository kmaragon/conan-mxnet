#include <iostream>
#include <mxnet/base.h>

int main() {
    mxnet::Context context;

    return context.real_dev_id();
}
