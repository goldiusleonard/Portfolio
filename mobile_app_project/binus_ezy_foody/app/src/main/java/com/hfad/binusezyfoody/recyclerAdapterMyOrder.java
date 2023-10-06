package com.hfad.binusezyfoody;

import android.content.Context;
import android.content.Intent;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import java.util.ArrayList;

public class recyclerAdapterMyOrder extends RecyclerView.Adapter<recyclerAdapterMyOrder.MyViewHolder> {
    private ArrayList<MyOrder> myOrderList;

    public recyclerAdapterMyOrder(ArrayList<MyOrder> myOrderList) {
        this.myOrderList = myOrderList;
    }

    public class MyViewHolder extends RecyclerView.ViewHolder {
        private TextView name;
        private TextView price;
        private TextView quantity;
        private Button addMyOrderBtn;
        private Button removeMyOrderBtn;
        private ImageView img;
        private final Context context;

        public MyViewHolder (final View view) {
            super(view);
            this.name = view.findViewById(R.id.name);
            this.price = view.findViewById(R.id.price);
            this.quantity = view.findViewById(R.id.quantity);
            this.img = view.findViewById(R.id.product_img);
            this.addMyOrderBtn = view.findViewById(R.id.addMyOrderBtn);
            this.removeMyOrderBtn = view.findViewById(R.id.removeMyOrderBtn);
            context = view.getContext();

            view.setOnClickListener(new View.OnClickListener() {

                @Override
                public void onClick(View v) {
                    MyOrder myOrder = myOrderList.get(getAdapterPosition());
                    Intent intent = new Intent(context, updateMyOrderActivity.class);
                    intent.putExtra("position", myOrder.getPosition());
                    intent.putExtra("type", myOrder.getType());

                    if(myOrder.getType().equals("Drink")) {
                        Drink drink = DrinkCatalogActivity.getDrink(myOrder.getPosition());

                        intent.putExtra("name", drink.getName());
                        intent.putExtra("price", drink.getPrice());
                        intent.putExtra("img", drink.getImg());
                    }
                    else if(myOrder.getType().equals("Snack")) {
                        Snack snack = SnackCatalogActivity.getSnack(myOrder.getPosition());

                        intent.putExtra("name", snack.getName());
                        intent.putExtra("price", snack.getPrice());
                        intent.putExtra("img", snack.getImg());
                    }
                    else {
                        Food food = FoodCatalogActivity.getFood(myOrder.getPosition());

                        intent.putExtra("name", food.getName());
                        intent.putExtra("price", food.getPrice());
                        intent.putExtra("img", food.getImg());
                    }

                    context.startActivity(intent);
                }
            });
        }

    }

    @NonNull
    @Override
    public recyclerAdapterMyOrder.MyViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View itemView = LayoutInflater.from(parent.getContext()).inflate(R.layout.my_order_item, parent, false);
        return new MyViewHolder(itemView);

    }

    @Override
    public void onBindViewHolder(@NonNull recyclerAdapterMyOrder.MyViewHolder holder, int position) {
        String type = myOrderList.get(position).getType();
        Integer pos = myOrderList.get(position).getPosition();
        Integer quantity = myOrderList.get(position).getQuantity();

        String name;
        Integer price = 0;
        int img;

        if(type.equals("Drink")) {
            Drink drink = DrinkCatalogActivity.getDrink(pos);
            name = drink.getName();
            price = drink.getPrice();
            img = drink.getImg();
        }
        else if (type.equals("Snack")) {
            Snack snack = SnackCatalogActivity.getSnack(pos);
            name = snack.getName();
            price = snack.getPrice();
            img = snack.getImg();
        }
        else {
            Food food = FoodCatalogActivity.getFood(pos);
            name = food.getName();
            price = food.getPrice();
            img = food.getImg();
        }

        Integer subtotalPrice = price * quantity;

        holder.name.setText(name);
        holder.price.setText(subtotalPrice.toString());
        holder.quantity.setText("Qty: " + quantity.toString());
        holder.img.setImageResource(img);
    }

    @Override
    public int getItemCount() {
        return myOrderList.size();
    }

    public int getTotalPrice() {
        int size = myOrderList.size();
        int totalPrice = 0;
        int price;
        int quantity;
        for(int i = 0; i < size; i++) {
            MyOrder item = myOrderList.get(i);
            String type = item.getType();
            Integer pos = item.getPosition();
            price = 0;

            if(type.equals("Drink")) {
                Drink drink = DrinkCatalogActivity.getDrink(pos);
                price = drink.getPrice();
            }
            else if (type.equals("Snack")) {
                Snack snack = SnackCatalogActivity.getSnack(pos);
                price = snack.getPrice();
            }
            else {
                Food food = FoodCatalogActivity.getFood(pos);
                price = food.getPrice();
            }

            quantity = item.getQuantity();
            totalPrice += (price * quantity);
        }
        return totalPrice;
    }

}
