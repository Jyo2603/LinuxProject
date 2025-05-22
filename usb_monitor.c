#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/usb.h>
#include <linux/notifier.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/slab.h>
#include <linux/string.h>

static int plug_count = 0;
static int unplug_count = 0;
static char last_vendor[16] = "None";
static char last_product[16] = "None";
static char last_power_path[128] = "N/A";
static char last_type[32] = "Unknown";

// USB event handler
static int usb_notify(struct notifier_block *nb, unsigned long action, void *data) {
    struct usb_device *udev = data;

    switch (action) {
        case USB_DEVICE_ADD:
            plug_count++;

            snprintf(last_vendor, sizeof(last_vendor), "0x%04x", le16_to_cpu(udev->descriptor.idVendor));
            snprintf(last_product, sizeof(last_product), "0x%04x", le16_to_cpu(udev->descriptor.idProduct));
            snprintf(last_power_path, sizeof(last_power_path), "/sys/bus/usb/devices/%s/power/control", udev->dev.kobj.name);

            // Default type
            strncpy(last_type, "Unknown", sizeof(last_type));

            // Check for mass storage class
            if (udev->actconfig && udev->actconfig->interface[0]) {
                struct usb_interface_descriptor desc = udev->actconfig->interface[0]->altsetting[0].desc;
                if (desc.bInterfaceClass == USB_CLASS_MASS_STORAGE) {
                    strncpy(last_type, "Mass Storage", sizeof(last_type));
                } else {
                    strncpy(last_type, "Non-Storage", sizeof(last_type));
                }
            }

            printk(KERN_INFO "[USB_MON] USB plugged in: Vendor=0x%04x, Product=0x%04x",
                   le16_to_cpu(udev->descriptor.idVendor),
                   le16_to_cpu(udev->descriptor.idProduct));
            break;

        case USB_DEVICE_REMOVE:
            unplug_count++;
            printk(KERN_INFO "[USB_MON] USB unplugged.");
            break;
    }

    return NOTIFY_OK;
}

// /proc interface
static int show_usb_info(struct seq_file *m, void *v) {
    seq_printf(m, "USB Monitor Stats:\n");
    seq_printf(m, "Plugged in count : %d\n", plug_count);
    seq_printf(m, "Unplugged count  : %d\n", unplug_count);
    seq_printf(m, "Last Vendor ID   : %s\n", last_vendor);
    seq_printf(m, "Last Product ID  : %s\n", last_product);
    seq_printf(m, "Device Type      : %s\n", last_type);
    seq_printf(m, "Power Control at : %s\n", last_power_path);
    return 0;
}

static int open_proc(struct inode *inode, struct file *file) {
    return single_open(file, show_usb_info, NULL);
}

static const struct proc_ops proc_fops = {
    .proc_open    = open_proc,
    .proc_read    = seq_read,
    .proc_release = single_release,
};

static struct notifier_block usb_nb = {
    .notifier_call = usb_notify
};

static int __init usb_init(void) {
    usb_register_notify(&usb_nb);
    proc_create("usb_monitor", 0, NULL, &proc_fops);
    printk(KERN_INFO "[USB_MON] USB Monitor module loaded.");
    return 0;
}

static void __exit usb_exit(void) {
    remove_proc_entry("usb_monitor", NULL);
    usb_unregister_notify(&usb_nb);
    printk(KERN_INFO "[USB_MON] USB Monitor module unloaded.");
}

module_init(usb_init);
module_exit(usb_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Jyotsna P");
MODULE_DESCRIPTION("USB Monitor with vendor/product info and type detection (safe version)");
