try:
    from store.tests.unit import test_checkout_views
    print("Import successful")
    print(dir(test_checkout_views))
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
